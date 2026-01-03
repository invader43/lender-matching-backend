from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Json
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from database import get_db, engine, Base
from models import Submission

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for validation
class SubmissionCreate(BaseModel):
    name: str
    email: str

    class Config:
        extra = "allow" # Allow other fields to be passed

@app.get("/form")
async def get_form_schema():
    """Returns the hardcoded schema."""
    return {
        "schema": {
            "name": "string",
            "email": "string",
            "business_name": "string",
            "loan_amount": "number"
        }
    }

@app.post("/form")
async def submit_form(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """Accepts a dictionary, validates basic fields, and saves to JSONB."""
    
    # Basic validation
    if "name" not in payload or "email" not in payload:
        raise HTTPException(status_code=422, detail="Missing 'name' or 'email' fields")

    # Create submission
    new_submission = Submission(data=payload)
    db.add(new_submission)
    await db.commit()
    await db.refresh(new_submission)

    return {"id": new_submission.id, "message": "Submission received"}

@app.get("/submissions")
async def get_submissions(db: AsyncSession = Depends(get_db)):
    """(Optional) Helper to view submissions"""
    result = await db.execute(select(Submission))
    submissions = result.scalars().all()
    return submissions
