"""
Smart Reconciliation Models
Database schema for missing cost basis detection and matching
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Numeric, DECIMAL, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.advanced_tax.integration.database import Base
from app.advanced_tax.models.shared import BaseModel, AuditTimestamp
from app.advanced_tax.utils import ReconciliationStatus


class MissingCostBasis(BaseModel):
    """
    Transaction with unknown cost basis.
    Represents a "gap" that needs to be filled.
    """
    __tablename__ = "missing_cost_basis"
    
    # User & transaction
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), index=True)
    transaction_id: Mapped[int] = mapped_column(Integer, nullable=True)  # FK to transaction
    
    # Transaction details
    asset: Mapped[str] = mapped_column(String(12), index=True)
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(20, 8))
    transaction_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    transaction_type: Mapped[str] = mapped_column(String(20))  # RECEIVE, TRANSFER_IN
    
    # Detection
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    error_description: Mapped[str] = mapped_column(Text)
    
    # Cost basis information
    status: Mapped[str] = mapped_column(
        String(20),
        default=ReconciliationStatus.PENDING,
        index=True
    )
    cost_basis: Mapped[Decimal] = mapped_column(DECIMAL(20, 2), nullable=True)
    cost_basis_source: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )  # matched_send, manual_entry, estimate, market_value
    
    # Matching
    matched_transaction_id: Mapped[int] = mapped_column(Integer, nullable=True)
    matched_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Financial impact
    current_estimated_value: Mapped[Decimal] = mapped_column(DECIMAL(20, 2))
    potential_tax_impact: Mapped[Decimal] = mapped_column(DECIMAL(20, 2))
    severity_score: Mapped[float] = mapped_column(Float)  # 0-1
    
    def __repr__(self):
        return f"<MissingCostBasis {self.asset} {self.status}>"


class ReconciliationMatch(BaseModel):
    """
    Links between send and receive transactions.
    Represents a successful match.
    """
    __tablename__ = "reconciliation_matches"
    
    # Linked transactions
    send_transaction_id: Mapped[int] = mapped_column(Integer, index=True)
    receive_transaction_id: Mapped[int] = mapped_column(Integer, index=True)
    
    # User
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), index=True)
    
    # Matching quality
    matching_score: Mapped[float] = mapped_column(Float)  # 0-1
    matched_by: Mapped[str] = mapped_column(String(20))  # user, system, ai_suggested
    
    # Details
    matching_reason: Mapped[str] = mapped_column(String(100))  # Why matched?
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Confirmation
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ReconciliationMatch score={self.matching_score:.2f}>"


class ReconciliationHistory(BaseModel):
    """
    Audit trail of all reconciliation actions.
    For compliance and debugging.
    """
    __tablename__ = "reconciliation_history"
    
    # Action details
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(50))  # match, manual_entry, dismiss, undo
    
    # What changed
    transaction_id: Mapped[int] = mapped_column(Integer, index=True)
    old_value: Mapped[str] = mapped_column(Text)  # JSON of before state
    new_value: Mapped[str] = mapped_column(Text)  # JSON of after state
    
    # Why
    reason: Mapped[str] = mapped_column(String(255))
    user_notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Revert capability
    is_reversible: Mapped[bool] = mapped_column(Boolean, default=True)
    reverted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ReconciliationHistory {self.action_type} txn={self.transaction_id}>"
