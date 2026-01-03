"""Policies API router - manages policy rules editing."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid

from database import get_db
from models.policies import Policy
from models.policy_rules import PolicyRule
from models.lenders import Lender
from schemas import PolicyResponse, PolicyRuleCreate, PolicyRuleResponse

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("", response_model=List[PolicyResponse])
async def get_all_policies(
    lender_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all policies, optionally filtered by lender.
    """
    query = select(Policy).options(selectinload(Policy.rules))
    if lender_id:
        query = query.where(Policy.lender_id == lender_id)
    
    result = await db.execute(query)
    policies = result.scalars().all()
    return policies


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific policy with all its rules."""
    result = await db.execute(
        select(Policy)
        .where(Policy.id == policy_id)
        .options(selectinload(Policy.rules))
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return policy


@router.patch("/{policy_id}")
async def update_policy(
    policy_id: uuid.UUID,
    name: Optional[str] = None,
    min_fit_score: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Update policy metadata (name, min_fit_score).
    """
    result = await db.execute(
        select(Policy)
        .where(Policy.id == policy_id)
        .options(selectinload(Policy.rules))
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    if name is not None:
        policy.name = name
    if min_fit_score is not None:
        policy.min_fit_score = min_fit_score
    
    await db.commit()
    await db.refresh(policy)
    
    return policy


@router.put("/{policy_id}/rules", response_model=List[PolicyRuleResponse])
async def update_policy_rules(
    policy_id: uuid.UUID,
    rules: List[PolicyRuleCreate],
    db: AsyncSession = Depends(get_db)
):
    """
    Update all rules for a policy.
    This is the human-in-the-loop editing endpoint.
    Replaces all existing rules with the provided ones.
    """
    # Verify policy exists
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Delete existing rules
    await db.execute(
        delete(PolicyRule).where(PolicyRule.policy_id == policy_id)
    )
    
    # Create new rules
    new_rules = []
    for rule_data in rules:
        rule = PolicyRule(
            policy_id=policy_id,
            **rule_data.model_dump()
        )
        db.add(rule)
        new_rules.append(rule)
    
    await db.commit()
    
    # Refresh to get IDs
    for rule in new_rules:
        await db.refresh(rule)
    
    return new_rules


@router.post("/{policy_id}/rules", response_model=PolicyRuleResponse, status_code=201)
async def add_single_rule(
    policy_id: uuid.UUID,
    rule: PolicyRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Add a single rule to a policy.
    """
    # Verify policy exists
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    new_rule = PolicyRule(
        policy_id=policy_id,
        **rule.model_dump()
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    
    return new_rule


@router.delete("/{policy_id}/rules/{rule_id}", status_code=204)
async def delete_single_rule(
    policy_id: uuid.UUID,
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a single rule from a policy.
    """
    result = await db.execute(
        select(PolicyRule).where(
            PolicyRule.id == rule_id,
            PolicyRule.policy_id == policy_id
        )
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    await db.delete(rule)
    await db.commit()
    
    return None


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a policy and all its rules."""
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    await db.delete(policy)
    await db.commit()
    
    return None

