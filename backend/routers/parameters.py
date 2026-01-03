"""Parameters API router - manages the parameter registry."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models.parameter_definitions import ParameterDefinition
from schemas import ParameterDefinitionCreate, ParameterDefinitionUpdate, ParameterDefinitionResponse

router = APIRouter(prefix="/parameters", tags=["parameters"])


@router.get("", response_model=List[ParameterDefinitionResponse])
async def get_parameters(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all parameter definitions.
    Used by frontend to dynamically build forms.
    """
    query = select(ParameterDefinition)
    if active_only:
        query = query.where(ParameterDefinition.is_active == True)
    
    result = await db.execute(query)
    parameters = result.scalars().all()
    return parameters


@router.post("", response_model=ParameterDefinitionResponse, status_code=201)
async def create_parameter(
    parameter: ParameterDefinitionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually create a new parameter definition.
    Admin endpoint for adding fields to the global schema.
    """
    # Check if parameter with same key_name already exists
    result = await db.execute(
        select(ParameterDefinition).where(
            ParameterDefinition.key_name == parameter.key_name
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Parameter with key_name '{parameter.key_name}' already exists"
        )
    
    new_parameter = ParameterDefinition(**parameter.model_dump())
    db.add(new_parameter)
    await db.commit()
    await db.refresh(new_parameter)
    
    return new_parameter


@router.get("/{key_name}", response_model=ParameterDefinitionResponse)
async def get_parameter(
    key_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific parameter definition by key name."""
    result = await db.execute(
        select(ParameterDefinition).where(
            ParameterDefinition.key_name == key_name
        )
    )
    parameter = result.scalar_one_or_none()
    
    if not parameter:
        raise HTTPException(
            status_code=404,
            detail=f"Parameter '{key_name}' not found"
        )
    
    return parameter


@router.put("/{key_name}", response_model=ParameterDefinitionResponse)
async def update_parameter(
    key_name: str,
    update_data: ParameterDefinitionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a parameter definition.
    Admin endpoint for modifying parameter properties.
    Note: key_name cannot be changed to maintain referential integrity.
    """
    result = await db.execute(
        select(ParameterDefinition).where(
            ParameterDefinition.key_name == key_name
        )
    )
    parameter = result.scalar_one_or_none()
    
    if not parameter:
        raise HTTPException(
            status_code=404,
            detail=f"Parameter '{key_name}' not found"
        )
    
    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(parameter, field, value)
    
    await db.commit()
    await db.refresh(parameter)
    
    return parameter


@router.delete("/{key_name}", status_code=204)
async def delete_parameter(
    key_name: str,
    hard_delete: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete or deactivate a parameter definition.
    By default, soft-deletes (sets is_active=False) to preserve rule references.
    Use hard_delete=True to permanently remove (will fail if rules reference it).
    """
    result = await db.execute(
        select(ParameterDefinition).where(
            ParameterDefinition.key_name == key_name
        )
    )
    parameter = result.scalar_one_or_none()
    
    if not parameter:
        raise HTTPException(
            status_code=404,
            detail=f"Parameter '{key_name}' not found"
        )
    
    if hard_delete:
        try:
            await db.delete(parameter)
            await db.commit()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete parameter: it may be referenced by rules. Error: {str(e)}"
            )
    else:
        # Soft delete
        parameter.is_active = False
        await db.commit()
    
    return None
