"""Validation utilities for dynamic form data."""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.parameter_definitions import ParameterDefinition, DataType


async def validate_form_data(form_data: dict, db: AsyncSession) -> None:
    """
    Validate form data against parameter definitions.
    Ensures all required fields are present and types match.
    
    Args:
        form_data: The dynamic form data to validate
        db: Database session
        
    Raises:
        HTTPException: If validation fails
    """
    # Get all active parameter definitions
    result = await db.execute(
        select(ParameterDefinition).where(ParameterDefinition.is_active == True)
    )
    parameters = result.scalars().all()
    
    # Create lookup dict
    param_dict = {p.key_name: p for p in parameters}
    
    # Validate each field in form_data
    for key, value in form_data.items():
        if key not in param_dict:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown parameter '{key}'. This field is not in the parameter registry."
            )
        
        param = param_dict[key]
        
        # Type validation
        if not _validate_type(value, param.data_type):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid type for parameter '{key}'. Expected {param.data_type}, got {type(value).__name__}"
            )
        
        # For select types, validate against options
        if param.data_type == DataType.SELECT and param.options:
            allowed_values = param.options.get('values', [])
            if value not in allowed_values:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid value for parameter '{key}'. Must be one of: {allowed_values}"
                )


def _validate_type(value: any, expected_type: DataType) -> bool:
    """
    Validate that a value matches the expected data type.
    
    Args:
        value: The value to validate
        expected_type: The expected DataType
        
    Returns:
        True if valid, False otherwise
    """
    if expected_type == DataType.STRING or expected_type == DataType.SELECT:
        return isinstance(value, str)
    elif expected_type == DataType.NUMBER or expected_type == DataType.CURRENCY:
        return isinstance(value, (int, float))
    elif expected_type == DataType.BOOLEAN:
        return isinstance(value, bool)
    else:
        return True  # Unknown type, allow it
