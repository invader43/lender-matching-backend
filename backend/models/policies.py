"""Policy model - lender programs/tiers."""

from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base

if TYPE_CHECKING:
    from .lenders import Lender
    from .policy_rules import PolicyRule
    from .match_results import MatchResult


class Policy(Base):
    """
    Policy - represents a lender program or tier.
    E.g., "Tier A - Preferred", "Equipment Finance Program"
    """
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    lender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lenders.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    min_fit_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    lender: Mapped["Lender"] = relationship("Lender", back_populates="policies")
    rules: Mapped[List["PolicyRule"]] = relationship(
        "PolicyRule",
        back_populates="policy",
        cascade="all, delete-orphan"
    )
    match_results: Mapped[List["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="policy",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Policy(id='{self.id}', name='{self.name}')>"
