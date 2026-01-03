"""Applications API router - manages loan applications and matching."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
import uuid

from database import get_db
from models.loan_applications import LoanApplication
from models.match_results import MatchResult
from models.policies import Policy
from models.lenders import Lender
from schemas import (
    LoanApplicationCreate,
    LoanApplicationResponse,
    MatchResultResponse
)
from services.matching_service import match_application
from utils.validators import validate_form_data

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=LoanApplicationResponse, status_code=201)
async def create_application(
    application: LoanApplicationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a loan application.
    Validates form data against parameter definitions and triggers matching.
    """
    # Validate form data against parameter definitions
    await validate_form_data(application.form_data, db)
    
    # Create application
    new_application = LoanApplication(**application.model_dump())
    db.add(new_application)
    await db.commit()
    await db.refresh(new_application)
    
    # Trigger background matching
    background_tasks.add_task(
        match_application,
        application_id=new_application.id
    )
    
    return new_application


@router.get("", response_model=List[LoanApplicationResponse])
async def get_applications(db: AsyncSession = Depends(get_db)):
    """Get all loan applications."""
    result = await db.execute(
        select(LoanApplication).order_by(LoanApplication.created_at.desc())
    )
    applications = result.scalars().all()
    return applications


@router.get("/{application_id}", response_model=LoanApplicationResponse)
async def get_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific application by ID."""
    result = await db.execute(
        select(LoanApplication).where(LoanApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return application


@router.get("/{application_id}/matches", response_model=List[MatchResultResponse])
async def get_application_matches(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get matching results for an application.
    Returns all lender matches sorted by fit score (descending).
    """
    # Verify application exists
    result = await db.execute(
        select(LoanApplication).where(LoanApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get match results with policy and lender info
    result = await db.execute(
        select(MatchResult)
        .where(MatchResult.application_id == application_id)
        .options(
            selectinload(MatchResult.policy).selectinload(Policy.lender)
        )
        .order_by(MatchResult.fit_score.desc())
    )
    matches = result.scalars().all()
    
    # Format response with lender and program names
    formatted_matches = []
    for match in matches:
        formatted_matches.append({
            "id": match.id,
            "application_id": match.application_id,
            "policy_id": match.policy_id,
            "lender_name": match.policy.lender.name,
            "program_name": match.policy.name,
            "eligible": match.eligible,
            "fit_score": match.fit_score,
            "evaluations": match.evaluations,
            "created_at": match.created_at
        })
    
    return formatted_matches
