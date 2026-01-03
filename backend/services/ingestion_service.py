"""PDF ingestion service - orchestrates the PDF processing workflow."""

import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from database import DATABASE_URL
from models.parameter_definitions import ParameterDefinition, DataType
from models.policies import Policy
from models.policy_rules import PolicyRule, RuleOperator, RuleType
from services.gemini_service import get_gemini_service


# Create async engine for background tasks
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


def convert_data_type(value: str) -> DataType:
    """Convert string to DataType enum."""
    mapping = {
        "string": DataType.STRING,
        "number": DataType.NUMBER,
        "boolean": DataType.BOOLEAN,
        "select": DataType.SELECT,
        "currency": DataType.CURRENCY,
    }
    return mapping.get(value.lower(), DataType.STRING)


def convert_rule_operator(value: str) -> RuleOperator:
    """Convert string to RuleOperator enum."""
    mapping = {
        "gt": RuleOperator.GT,
        "lt": RuleOperator.LT,
        "eq": RuleOperator.EQ,
        "neq": RuleOperator.NEQ,
        "gte": RuleOperator.GTE,
        "lte": RuleOperator.LTE,
        "in": RuleOperator.IN,
        "contains": RuleOperator.CONTAINS,
    }
    return mapping.get(value.lower(), RuleOperator.EQ)


def convert_rule_type(value: str) -> RuleType:
    """Convert string to RuleType enum."""
    mapping = {
        "eligibility": RuleType.ELIGIBILITY,
        "scoring": RuleType.SCORING,
    }
    return mapping.get(value.lower(), RuleType.ELIGIBILITY)


async def process_lender_pdf(
    lender_id: uuid.UUID,
    file: UploadFile,
    task_id: str
):
    """
    Background task to process a lender PDF.
    
    Steps:
    1. Save PDF to disk
    2. Fetch current parameter definitions
    3. Call Gemini service to extract rules
    4. Create new parameters if needed
    5. Create policy and rules in database
    
    Args:
        lender_id: ID of the lender
        file: Uploaded PDF file
        task_id: Unique task identifier
    """
    pdf_path = None
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save PDF to disk
        pdf_filename = f"{task_id}_{file.filename}"
        pdf_path = upload_dir / pdf_filename
        
        async with aiofiles.open(pdf_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Get database session
        async with SessionLocal() as db:
            # Fetch current parameter definitions
            result = await db.execute(
                select(ParameterDefinition).where(ParameterDefinition.is_active == True)
            )
            parameters = result.scalars().all()
            
            # Convert to dict format for Gemini
            current_parameters = [
                {
                    "key_name": p.key_name,
                    "display_label": p.display_label,
                    "data_type": p.data_type.value,
                    "description": p.description
                }
                for p in parameters
            ]
            
            # Call Gemini service
            gemini_service = get_gemini_service()
            extraction_result = await gemini_service.extract_rules_from_pdf(
                str(pdf_path),
                current_parameters
            )
            
            # Create new parameters if needed
            param_map = {p.key_name: p for p in parameters}
            
            for new_param in extraction_result.get("new_parameters", []):
                if new_param["key_name"] not in param_map:
                    parameter = ParameterDefinition(
                        key_name=new_param["key_name"],
                        display_label=new_param["display_label"],
                        data_type=convert_data_type(new_param["data_type"]),  # Convert to enum
                        options=new_param.get("options"),
                        description=new_param.get("description"),
                        is_active=True
                    )
                    db.add(parameter)
                    param_map[new_param["key_name"]] = parameter
            
            await db.commit()
            
            # Create policy
            policy_name = f"Policy from {file.filename}"
            policy = Policy(
                lender_id=lender_id,
                name=policy_name,
                min_fit_score=0
            )
            db.add(policy)
            await db.flush()  # Get policy ID
            
            # Create rules
            for rule_data in extraction_result.get("rules", []):
                rule = PolicyRule(
                    policy_id=policy.id,
                    parameter_key=rule_data["parameter"],
                    operator=convert_rule_operator(rule_data["operator"]),  # Convert to enum
                    value_comparison=rule_data["value"],
                    rule_type=convert_rule_type(rule_data["type"]),  # Convert to enum
                    weight=rule_data.get("weight", 0),
                    failure_reason=rule_data.get("reason")
                )
                db.add(rule)
            
            await db.commit()
            
            print(f"✅ Successfully processed PDF for lender {lender_id}")
            print(f"   Created policy: {policy.name}")
            print(f"   Extracted {len(extraction_result['rules'])} rules")
            print(f"   Created {len(extraction_result.get('new_parameters', []))} new parameters")
            
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up PDF file
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except:
                pass

