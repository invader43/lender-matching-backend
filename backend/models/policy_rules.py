"""Policy rules model - normalized underwriting rules."""

from typing import Optional, Any, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum
from database import Base

if TYPE_CHECKING:
    from .policies import Policy


class RuleOperator(str, enum.Enum):
    """Comparison operators for rule evaluation."""
    GT = "gt"      # Greater than
    LT = "lt"      # Less than
    EQ = "eq"      # Equal to
    NEQ = "neq"    # Not equal to
    GTE = "gte"    # Greater than or equal
    LTE = "lte"    # Less than or equal
    IN = "in"      # In list
    CONTAINS = "contains"  # Contains substring/value


class RuleType(str, enum.Enum):
    """Type of rule - eligibility (knockout) or scoring (points)."""
    ELIGIBILITY = "eligibility"
    SCORING = "scoring"


class PolicyRule(Base):
    """
    Policy Rule - individual underwriting rule extracted from PDF.
    Normalized storage linking to parameter definitions.
    """
    __tablename__ = "policy_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False
    )
    parameter_key: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("parameter_definitions.key_name", ondelete="CASCADE"),
        nullable=False
    )
    operator: Mapped[RuleOperator] = mapped_column(
        SQLEnum(RuleOperator, name="rule_operator_enum"),
        nullable=False
    )
    value_comparison: Mapped[Any] = mapped_column(
        JSONB, 
        nullable=False
    )
    rule_type: Mapped[RuleType] = mapped_column(
        SQLEnum(RuleType, name="rule_type_enum"),
        nullable=False
    )
    weight: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    policy: Mapped["Policy"] = relationship("Policy", back_populates="rules")

    def __repr__(self):
        return f"<PolicyRule(parameter='{self.parameter_key}', operator='{self.operator}')>"
