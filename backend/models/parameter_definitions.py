"""Parameter definitions model - the global schema registry."""

from typing import Optional
from sqlalchemy import String, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum
from database import Base


class DataType(str, enum.Enum):
    """Supported data types for parameters."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"
    CURRENCY = "currency"


class ParameterDefinition(Base):
    """
    Parameter Registry - defines all available fields in the system.
    This drives dynamic form generation on the frontend.
    """
    __tablename__ = "parameter_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    key_name: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False,
        index=True
    )
    display_label: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[DataType] = mapped_column(
        SQLEnum(DataType, name="data_type_enum"),
        nullable=False
    )
    options: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<ParameterDefinition(key_name='{self.key_name}', type='{self.data_type}')>"
