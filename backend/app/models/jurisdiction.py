"""
Latin American Tax Jurisdiction Models
Models for tax jurisdictions, tax rules, and tax forms
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Numeric, Integer, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db import Base


class Jurisdiction(Base):
    """
    Represents a tax jurisdiction (country)
    Supported: Mexico (MX), Brazil (BR), Argentina (AR), Colombia (CO), Peru (PE), Chile (CL)
    """
    __tablename__ = "tax_jurisdictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(3), unique=True, nullable=False, index=True)  # MX, BR, AR, CO, PE, CL
    name = Column(String(100), nullable=False)
    region = Column(String(50), nullable=False)  # 'Latin America'
    
    # Tax rates
    # For simple cases; for progressive rates use tax_rules
    capital_gains_rate = Column(Numeric(5, 2), nullable=True)  # Default CG rate if no tiers
    ordinary_income_rate = Column(Numeric(5, 2), nullable=True)
    vat_rate = Column(Numeric(5, 2), nullable=False)  # VAT/IVA rate
    
    # Rules
    reporting_currency = Column(String(3), nullable=False)  # USD, MXN, BRL, ARS, COP, PEN, CLP
    holding_period_days = Column(Integer, nullable=False, default=365)
    crypto_classification = Column(Text, nullable=True)
    
    # Filing
    filing_frequency = Column(String(50), nullable=False)  # 'yearly', 'quarterly', 'monthly'
    filing_authority = Column(String(100), nullable=False)
    filing_url = Column(Text, nullable=True)
    
    # API Integration
    tax_authority_api_url = Column(Text, nullable=True)
    api_requires_auth = Column(Boolean, default=False)
    
    # Relationships
    tax_rules = relationship("TaxRule", back_populates="jurisdiction", cascade="all, delete-orphan")
    tax_form_templates = relationship("TaxFormTemplate", back_populates="jurisdiction", cascade="all, delete-orphan")
    user_profiles = relationship("UserTaxProfile", back_populates="jurisdiction", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Jurisdiction {self.code}: {self.name}>"


class TaxRule(Base):
    """
    Tax rule for a specific transaction type in a jurisdiction
    Handles: transaction type → tax category → calculation method
    """
    __tablename__ = "tax_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey("tax_jurisdictions.id"), nullable=False, index=True)
    
    # Classification
    transaction_type = Column(String(50), nullable=False)  # 'trade', 'deposit', 'withdrawal', 'income', 'fee', 'airdrop'
    tax_category = Column(String(50), nullable=False)  # 'capital_gains', 'ordinary_income', 'vat_base', 'exempt'
    
    # Calculation method
    calculation_method = Column(String(50), nullable=False)  # 'fifo', 'lifo', 'average_cost', 'specific_id'
    
    # Progressive tax tiers
    # [{"min": 0, "max": 100000, "rate": 0.05}, {"min": 100000, "max": 250000, "rate": 0.12}, ...]
    rate_tiers = Column(JSON, nullable=True)
    
    # Holding period treatment
    holding_period_treatment = Column(String(50), nullable=True)  # 'short_term', 'long_term'
    holding_period_days = Column(Integer, nullable=True)
    
    # Thresholds
    exclusion_threshold = Column(Numeric(15, 2), nullable=True)  # Min income to file
    
    # Special rules
    description = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    
    # Relationship
    jurisdiction = relationship("Jurisdiction", back_populates="tax_rules")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TaxRule {self.jurisdiction_id}: {self.transaction_type}>"


class TaxFormTemplate(Base):
    """
    Tax form template for PDF/XML generation
    Stores form metadata and structure
    """
    __tablename__ = "tax_form_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey("tax_jurisdictions.id"), nullable=False, index=True)
    
    # Form metadata
    form_id = Column(String(50), nullable=False)  # 'F573', '1880', '8949', 'IRPF', 'RFC'
    form_name = Column(String(200), nullable=False)
    
    # Templates
    pdf_template_path = Column(String(255), nullable=True)
    xml_schema_path = Column(String(255), nullable=True)
    csv_export_fields = Column(JSON, nullable=True)  # Column definitions
    
    # Form structure
    sections = Column(JSON, nullable=True)  # [{"name": "Capital Gains", "fields": [...]}]
    required_fields = Column(JSON, nullable=True)
    conditional_fields = Column(JSON, nullable=True)
    
    # Relationship
    jurisdiction = relationship("Jurisdiction", back_populates="tax_form_templates")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TaxFormTemplate {self.form_id}: {self.form_name}>"
