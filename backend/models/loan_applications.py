"""Loan application model - dynamic form data storage."""

from typing import Dict, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum
from database import Base

if TYPE_CHECKING:
    from .match_results import MatchResult


class ApplicationStatus(str, enum.Enum):
    """Status of loan application processing."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LoanApplication(Base):
    """
    Loan Application - stores dynamic form data as JSONB.
    The schema adapts based on parameter_definitions.
    """
    __tablename__ = "loan_applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    applicant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    form_data: Mapped[Dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus, name="application_status_enum"),
        default=ApplicationStatus.PROCESSING,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )

    # Relationships
    match_results: Mapped[List["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="application",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<LoanApplication(id='{self.id}', applicant='{self.applicant_name}')>"
