"""
Dynamic Lender Matching System - FastAPI Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import engine, Base
from routers import (
    parameters_router,
    lenders_router,
    policies_router,
    applications_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - create tables on startup."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Dynamic Lender Matching API",
    description="AI-powered lender matching system with dynamic schema",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(parameters_router)
app.include_router(lenders_router)
app.include_router(policies_router)
app.include_router(applications_router)


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "Dynamic Lender Matching API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "parameters": "/parameters",
            "lenders": "/lenders",
            "policies": "/policies",
            "applications": "/applications"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
