"""
Shared Models for Advanced Tax Engine
Base classes and common patterns
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.advanced_tax.integration.database import Base


class BaseModel(Base):
    """
    Abstract base model for all Advanced Tax Engine entities.
    Provides common fields and audit trails.
    """
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Metadata
    metadata_json: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=True
    )
    
    def to_dict(self):
        """Convert model to dict"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class AuditTimestamp(BaseModel):
    """Mixin for audit timestamp tracking"""
    __abstract__ = True
    
    # Who made the change
    changed_by_user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    change_reason: Mapped[str] = mapped_column(String, nullable=True)
    
    # Track changes
    previous_state: Mapped[dict] = mapped_column(JSON, nullable=True)
