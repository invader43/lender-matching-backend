"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any
from datetime import datetime
import uuid


# Parameter Definitions Schemas
class ParameterDefinitionBase(BaseModel):
    key_name: str = Field(..., max_length=100)
    display_label: str = Field(..., max_length=255)
    data_type: str = Field(..., pattern="^(string|number|boolean|select|currency)$")
    options: Optional[dict] = None
    description: Optional[str] = None
    is_active: bool = True


class ParameterDefinitionCreate(ParameterDefinitionBase):
    pass


class ParameterDefinitionUpdate(BaseModel):
    """Schema for updating parameter definitions. All fields optional."""
    display_label: Optional[str] = Field(None, max_length=255)
    data_type: Optional[str] = Field(None, pattern="^(string|number|boolean|select|currency)$")
    options: Optional[dict] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ParameterDefinitionResponse(ParameterDefinitionBase):
    id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)


# Lender Schemas
class LenderBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None


class LenderCreate(LenderBase):
    pass


class LenderResponse(LenderBase):
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Policy Schemas
class PolicyRuleBase(BaseModel):
    parameter_key: str
    operator: str = Field(..., pattern="^(gt|lt|eq|neq|gte|lte|in|contains)$")
    value_comparison: Any
    rule_type: str = Field(..., pattern="^(eligibility|scoring)$")
    weight: int = 0
    failure_reason: Optional[str] = None


class PolicyRuleCreate(PolicyRuleBase):
    pass


class PolicyRuleResponse(PolicyRuleBase):
    id: uuid.UUID
    policy_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)


class PolicyBase(BaseModel):
    name: str = Field(..., max_length=100)
    min_fit_score: int = 0


class PolicyCreate(PolicyBase):
    lender_id: uuid.UUID


class PolicyResponse(PolicyBase):
    id: uuid.UUID
    lender_id: uuid.UUID
    created_at: datetime
    last_updated: datetime
    rules: list[PolicyRuleResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class PolicyWithLenderResponse(PolicyResponse):
    lender_name: str


# Loan Application Schemas
class LoanApplicationCreate(BaseModel):
    applicant_name: str = Field(..., max_length=255)
    form_data: dict = Field(..., description="Dynamic form data based on parameter definitions")


class LoanApplicationResponse(BaseModel):
    id: uuid.UUID
    applicant_name: str
    form_data: dict
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Match Result Schemas
class RuleEvaluationResult(BaseModel):
    rule_id: uuid.UUID
    parameter_key: str
    parameter_label: str
    operator: str
    passed: bool
    actual_value: Any
    threshold_value: Any
    failure_reason: Optional[str] = None


class MatchResultResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    policy_id: uuid.UUID
    lender_name: str
    program_name: str
    eligible: bool
    fit_score: int
    evaluations: list[RuleEvaluationResult]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Ingestion Schemas
class IngestionTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
