"""
Seed script to initialize parameter definitions
Run this to create initial parameters in the database
"""

import asyncio
from sqlalchemy import select
from database import SessionLocal
from models.parameter_definitions import ParameterDefinition, DataType


async def seed_parameters():
    """Create initial parameter definitions."""
    
    parameters = [
        {
            "key_name": "fico_score",
            "display_label": "FICO Credit Score",
            "data_type": DataType.NUMBER,
            "description": "Personal credit score (300-850)",
            "is_active": True
        },
        {
            "key_name": "annual_revenue",
            "display_label": "Annual Revenue",
            "data_type": DataType.CURRENCY,
            "description": "Business annual revenue in dollars",
            "is_active": True
        },
        {
            "key_name": "years_in_business",
            "display_label": "Years in Business",
            "data_type": DataType.NUMBER,
            "description": "How many years has the business been operating",
            "is_active": True
        },
        {
            "key_name": "business_type",
            "display_label": "Business Type",
            "data_type": DataType.SELECT,
            "options": {
                "values": ["Trucking", "Construction", "Manufacturing", "Retail", "Services", "Other"]
            },
            "description": "Type of business",
            "is_active": True
        },
        {
            "key_name": "loan_amount",
            "display_label": "Loan Amount Requested",
            "data_type": DataType.CURRENCY,
            "description": "Amount of funding requested",
            "is_active": True
        },
        {
            "key_name": "has_bankruptcy",
            "display_label": "Bankruptcy in Last 7 Years",
            "data_type": DataType.BOOLEAN,
            "description": "Has the business or owner filed for bankruptcy in the last 7 years?",
            "is_active": True
        },
        {
            "key_name": "collateral_available",
            "display_label": "Collateral Available",
            "data_type": DataType.BOOLEAN,
            "description": "Do you have collateral to secure the loan?",
            "is_active": True
        },
    ]
    
    async with SessionLocal() as db:
        # Check if parameters already exist
        result = await db.execute(select(ParameterDefinition))
        existing = result.scalars().all()
        
        if existing:
            print(f"⚠️  {len(existing)} parameters already exist. Skipping seed.")
            return
        
        # Create parameters
        for param_data in parameters:
            param = ParameterDefinition(**param_data)
            db.add(param)
        
        await db.commit()
        print(f"✅ Created {len(parameters)} parameter definitions")
        
        for param_data in parameters:
            print(f"   - {param_data['display_label']} ({param_data['data_type'].value})")


if __name__ == "__main__":
    print("🌱 Seeding parameter definitions...")
    asyncio.run(seed_parameters())
    print("✨ Done!")
