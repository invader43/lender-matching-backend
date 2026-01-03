"""Match results model - stores matching outcomes."""

from typing import Dict, TYPE_CHECKING
from sqlalchemy import Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from database import Base

if TYPE_CHECKING:
    from .loan_applications import LoanApplication
    from .policies import Policy


class MatchResult(Base):
    """
    Match Result - stores the outcome of matching an application against a policy.
    Includes detailed evaluation breakdown.
    """
    __tablename__ = "match_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("loan_applications.id", ondelete="CASCADE"),
        nullable=False
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False
    )
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    fit_score: Mapped[int] = mapped_column(Integer, nullable=False)
    evaluations: Mapped[Dict] = mapped_column(
        JSONB, 
        nullable=False,
        comment="Detailed breakdown of each rule evaluation"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )

    # Relationships
    application: Mapped["LoanApplication"] = relationship(
        "LoanApplication", 
        back_populates="match_results"
    )
    policy: Mapped["Policy"] = relationship("Policy", back_populates="match_results")

    def __repr__(self):
        return f"<MatchResult(app_id='{self.application_id}', eligible={self.eligible})>"
