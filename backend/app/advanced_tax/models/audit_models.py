"""
Audit Trail & Export Models
Database schema for verified rules and audit packages
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Numeric, DECIMAL, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.advanced_tax.integration.database import Base
from app.advanced_tax.models.shared import BaseModel
from app.advanced_tax.utils import AuditStatus


class VerifiedTaxRule(BaseModel):
    """
    Tax rules verified and approved by professional accountants.
    These rules have expert endorsement.
    """
    __tablename__ = "verified_tax_rules"
    
    # Rule identification
    rule_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # MX_ISR_002
    rule_name: Mapped[str] = mapped_column(String(255))  # "ISR Progressive Income Tax"
    
    # Scope
    country: Mapped[str] = mapped_column(String(2), index=True)  # MX, BR, AR
    tax_type: Mapped[str] = mapped_column(String(50), index=True)  # INCOME_TAX, CAPITAL_GAINS
    
    # Rule definition
    rule_definition: Mapped[str] = mapped_column(Text)  # JSON or structured format
    
    # Legal reference
    law_reference: Mapped[str] = mapped_column(String(255))  # "Lei do Imposto de Renda"
    law_link: Mapped[str] = mapped_column(String(500), nullable=True)  # URL to official source
    tax_authority: Mapped[str] = mapped_column(String(100))  # "Receita Federal", "SAT"
    
    # Verification
    verified_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    verified_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    
    # Status & versioning
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, deprecated, under_review
    effective_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # When rule expires
    
    # Notes
    notes: Mapped[str] = mapped_column(Text, nullable=True)  # Explanation from accountant
    examples: Mapped[str] = mapped_column(Text, nullable=True)  # JSON with examples
    
    # Review tracking
    last_reviewed: Mapped[datetime] = mapped_column(DateTime)
    review_frequency: Mapped[str] = mapped_column(String(20), default="quarterly")  # How often reviewed
    next_review_date: Mapped[datetime] = mapped_column(DateTime)
    
    # Badge/branding
    can_use_verified_badge: Mapped[bool] = mapped_column(Boolean, default=True)
    
    def __repr__(self):
        return f"<VerifiedTaxRule {self.rule_code} v{self.version}>"


class CalculationAuditRecord(BaseModel):
    """
    Complete audit trail for every tax calculation.
    Shows what was calculated, why, and by which rule.
    """
    __tablename__ = "calculation_audit_records"
    
    # The transaction being calculated
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), index=True)
    transaction_id: Mapped[int] = mapped_column(Integer, nullable=True)  # Optional link to transaction
    
    # Transaction details
    asset: Mapped[str] = mapped_column(String(12), index=True)
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(20, 8))
    buy_price: Mapped[Decimal] = mapped_column(DECIMAL(20, 8))
    sell_price: Mapped[Decimal] = mapped_column(DECIMAL(20, 8))
    
    # Calculation details
    tax_type: Mapped[str] = mapped_column(String(50), index=True)  # What kind of tax?
    tax_rate: Mapped[Decimal] = mapped_column(DECIMAL(5, 4))  # 0.3000 for 30%
    calculated_tax: Mapped[Decimal] = mapped_column(DECIMAL(20, 2))  # Final tax amount
    
    # The rule applied
    applied_rule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("verified_tax_rules.id"),
        index=True
    )
    
    # Reasoning
    reasoning: Mapped[str] = mapped_column(Text)  # Why this rule? Why this rate?
    calculation_method: Mapped[str] = mapped_column(String(100))  # FIFO, AVERAGE_COST, etc.
    
    # Verification
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[str] = mapped_column(String(255), nullable=True)  # Accountant email
    verified_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Dispute tracking
    disputed: Mapped[bool] = mapped_column(Boolean, default=False)
    dispute_reason: Mapped[str] = mapped_column(Text, nullable=True)
    final_calculation: Mapped[Decimal] = mapped_column(DECIMAL(20, 2), nullable=True)  # If changed
    
    # Country context
    country: Mapped[str] = mapped_column(String(2), index=True)
    
    def __repr__(self):
        return f"<CalculationAuditRecord {self.asset} τ{self.calculated_tax}>"


class AuditPackage(BaseModel):
    """
    Complete audit export for a user/time period.
    Ready for tax authority submission.
    """
    __tablename__ = "audit_packages"
    
    # Scope
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), index=True)
    country: Mapped[str] = mapped_column(String(2), index=True)
    tax_year: Mapped[int] = mapped_column(Integer, index=True)
    
    # Content summary
    transaction_count: Mapped[int] = mapped_column(Integer)
    calculation_count: Mapped[int] = mapped_column(Integer)
    total_tax_calculated: Mapped[Decimal] = mapped_column(DECIMAL(20, 2))
    
    # Export details
    exported_file_path: Mapped[str] = mapped_column(Text)  # S3 or local path
    file_format: Mapped[str] = mapped_column(String(20))  # PDF, JSON, Excel
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Generation
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    generated_by_system_version: Mapped[str] = mapped_column(String(20))
    generated_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    
    # Verification
    status: Mapped[str] = mapped_column(
        String(20),
        default=AuditStatus.READY,
        index=True
    )
    verifying_accountant_id: Mapped[int] = mapped_column(Integer, nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Integrity
    content_hash: Mapped[str] = mapped_column(String(256), nullable=True)  # SHA256
    encryption_key: Mapped[str] = mapped_column(String(255), nullable=True)  # For secure storage
    
    # Timestamps
    downloaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    submitted_to_authority: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<AuditPackage {self.country} {self.tax_year} τ{self.total_tax_calculated}>"
