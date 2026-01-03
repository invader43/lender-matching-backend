"""Lenders API router - manages lenders and PDF ingestion."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
import uuid

from database import get_db
from models.lenders import Lender
from models.policies import Policy
from schemas import (
    LenderCreate, 
    LenderResponse, 
    PolicyResponse,
    IngestionTaskResponse
)
from services.ingestion_service import process_lender_pdf

router = APIRouter(prefix="/lenders", tags=["lenders"])


@router.post("", response_model=LenderResponse, status_code=201)
async def create_lender(
    lender: LenderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new lender."""
    new_lender = Lender(**lender.model_dump())
    db.add(new_lender)
    await db.commit()
    await db.refresh(new_lender)
    
    return new_lender


@router.get("", response_model=List[LenderResponse])
async def get_lenders(db: AsyncSession = Depends(get_db)):
    """Get all lenders."""
    result = await db.execute(select(Lender))
    lenders = result.scalars().all()
    return lenders


@router.get("/{lender_id}", response_model=LenderResponse)
async def get_lender(
    lender_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific lender by ID."""
    result = await db.execute(
        select(Lender).where(Lender.id == lender_id)
    )
    lender = result.scalar_one_or_none()
    
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    
    return lender


@router.post("/{lender_id}/ingest-guidelines", response_model=IngestionTaskResponse)
async def ingest_lender_guidelines(
    lender_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a PDF with lender guidelines for processing.
    Triggers background task to extract rules using Gemini.
    """
    # Verify lender exists
    result = await db.execute(
        select(Lender).where(Lender.id == lender_id)
    )
    lender = result.scalar_one_or_none()
    
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Add background task
    background_tasks.add_task(
        process_lender_pdf,
        lender_id=lender_id,
        file=file,
        task_id=task_id
    )
    
    return IngestionTaskResponse(
        task_id=task_id,
        status="processing",
        message="PDF ingestion started. This may take 10-30 seconds."
    )


@router.get("/{lender_id}/policies", response_model=List[PolicyResponse])
async def get_lender_policies(
    lender_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all policies for a lender with their rules."""
    result = await db.execute(
        select(Policy)
        .where(Policy.lender_id == lender_id)
        .options(selectinload(Policy.rules))
    )
    policies = result.scalars().all()
    
    return policies
