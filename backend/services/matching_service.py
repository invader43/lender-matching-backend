"""Matching service - evaluates applications against lender policies."""

import uuid
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import DATABASE_URL
from models.loan_applications import LoanApplication, ApplicationStatus
from models.policies import Policy
from models.policy_rules import PolicyRule, RuleOperator
from models.match_results import MatchResult
from models.parameter_definitions import ParameterDefinition


# Create async engine for background tasks
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def match_application(application_id: uuid.UUID):
    """
    Background task to match an application against all lender policies.
    
    Steps:
    1. Load application form data
    2. Fetch all active policies with rules
    3. Evaluate each policy's rules
    4. Calculate fit score
    5. Store results in match_results table
    6. Update application status
    
    Args:
        application_id: ID of the application to match
    """
    try:
        async with SessionLocal() as db:
            # Load application
            result = await db.execute(
                select(LoanApplication).where(LoanApplication.id == application_id)
            )
            application = result.scalar_one_or_none()
            
            if not application:
                print(f"❌ Application {application_id} not found")
                return
            
            form_data = application.form_data
            
            # Fetch all policies with rules
            result = await db.execute(
                select(Policy).options(selectinload(Policy.rules))
            )
            policies = result.scalars().all()
            
            # Fetch parameter definitions for labels
            result = await db.execute(select(ParameterDefinition))
            parameters = result.scalars().all()
            param_labels = {p.key_name: p.display_label for p in parameters}
            
            # Evaluate each policy
            for policy in policies:
                evaluations = []
                eligible = True
                total_score = 0
                max_score = 0
                
                for rule in policy.rules:
                    evaluation = evaluate_rule(rule, form_data, param_labels)
                    evaluations.append(evaluation)
                    
                    # Check eligibility rules
                    if rule.rule_type.value == "eligibility" and not evaluation["passed"]:
                        eligible = False
                    
                    # Calculate scoring
                    if rule.rule_type.value == "scoring":
                        max_score += rule.weight
                        if evaluation["passed"]:
                            total_score += rule.weight
                
                # Calculate fit score (0-100)
                if max_score > 0:
                    fit_score = int((total_score / max_score) * 100)
                else:
                    fit_score = 100 if eligible else 0
                
                # Store match result
                match_result = MatchResult(
                    application_id=application_id,
                    policy_id=policy.id,
                    eligible=eligible,
                    fit_score=fit_score,
                    evaluations=evaluations
                )
                db.add(match_result)
            
            # Update application status
            application.status = ApplicationStatus.COMPLETED
            
            await db.commit()
            
            print(f"✅ Successfully matched application {application_id}")
            print(f"   Evaluated against {len(policies)} policies")
            
    except Exception as e:
        print(f"❌ Error matching application: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Update application status to failed
        try:
            async with SessionLocal() as db:
                result = await db.execute(
                    select(LoanApplication).where(LoanApplication.id == application_id)
                )
                application = result.scalar_one_or_none()
                if application:
                    application.status = ApplicationStatus.FAILED
                    await db.commit()
        except:
            pass


def evaluate_rule(
    rule: PolicyRule,
    form_data: Dict[str, Any],
    param_labels: Dict[str, str]
) -> Dict[str, Any]:
    """
    Evaluate a single rule against application data.
    
    Args:
        rule: The policy rule to evaluate
        form_data: Application form data
        param_labels: Mapping of parameter keys to display labels
        
    Returns:
        Dictionary with evaluation result
    """
    parameter_key = rule.parameter_key
    actual_value = form_data.get(parameter_key)
    threshold_value = rule.value_comparison
    operator = rule.operator
    
    # Check if parameter exists in form data
    if actual_value is None:
        return {
            "rule_id": str(rule.id),
            "parameter_key": parameter_key,
            "parameter_label": param_labels.get(parameter_key, parameter_key),
            "operator": operator.value,
            "passed": False,
            "actual_value": None,
            "threshold_value": threshold_value,
            "failure_reason": f"Missing required field: {param_labels.get(parameter_key, parameter_key)}"
        }
    
    # Evaluate based on operator
    passed = False
    
    try:
        if operator == RuleOperator.GT:
            passed = actual_value > threshold_value
        elif operator == RuleOperator.LT:
            passed = actual_value < threshold_value
        elif operator == RuleOperator.EQ:
            passed = actual_value == threshold_value
        elif operator == RuleOperator.NEQ:
            passed = actual_value != threshold_value
        elif operator == RuleOperator.GTE:
            passed = actual_value >= threshold_value
        elif operator == RuleOperator.LTE:
            passed = actual_value <= threshold_value
        elif operator == RuleOperator.IN:
            passed = actual_value in threshold_value
        elif operator == RuleOperator.CONTAINS:
            passed = threshold_value in str(actual_value)
    except Exception as e:
        print(f"⚠️  Error evaluating rule: {e}")
        passed = False
    
    # Build failure reason if not passed
    failure_reason = None
    if not passed and rule.failure_reason:
        failure_reason = rule.failure_reason
    elif not passed:
        failure_reason = f"{param_labels.get(parameter_key, parameter_key)}: {actual_value} does not meet requirement ({operator.value} {threshold_value})"
    
    return {
        "rule_id": str(rule.id),
        "parameter_key": parameter_key,
        "parameter_label": param_labels.get(parameter_key, parameter_key),
        "operator": operator.value,
        "passed": passed,
        "actual_value": actual_value,
        "threshold_value": threshold_value,
        "failure_reason": failure_reason
    }
