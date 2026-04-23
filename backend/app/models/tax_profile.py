"""
User Tax Profile Models
Stores user-specific tax information per jurisdiction
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db import Base


class UserTaxProfile(Base):
    """
    User's tax profile for a specific jurisdiction
    Stores tax ID, preferences, and filing information
    """
    __tablename__ = "user_tax_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey("tax_jurisdictions.id"), nullable=False, index=True)
    
    jurisdiction = relationship("Jurisdiction", back_populates="user_profiles")
    
    # Personal tax information (encrypted at rest)
    tax_id = Column(String(50), nullable=True)  # RFC (Mexico), CPF (Brazil), CUIT (Argentina), etc.
    tax_payer_name = Column(String(255), nullable=True)
    tax_address = Column(Text, nullable=True)
    
    # Filing preferences
    fiscal_year_start_month = Column(Integer, default=1, nullable=False)
    fiscal_year_end_month = Column(Integer, default=12, nullable=False)
    
    # Tax treatment settings
    calculation_method = Column(String(50), default="fifo", nullable=False)  # fifo, lifo, average_cost
    preferred_tax_category = Column(String(50), nullable=True)  # capital_gains, ordinary_income, etc.
    
    # Export preferences
    # ['PDF', 'XML', 'CSV', 'ODS']
    preferred_export_formats = Column(String(255), default="PDF,CSV", nullable=False)
    
    # Professional contact
    tax_advisor_email = Column(String(255), nullable=True)
    tax_advisor_name = Column(String(255), nullable=True)
    
    # Filing tracking
    last_filed_year = Column(Integer, nullable=True)
    last_filed_date = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserTaxProfile user={self.user_id} jurisdiction={self.jurisdiction_id}>"
