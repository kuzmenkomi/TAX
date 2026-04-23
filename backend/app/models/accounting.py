from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db import Base

class LotMatch(Base):
    """
    Detailed log of which buy/receive lot was used to cover which sell/send/swap.
    This provides the 'Audit Trail' or 'Explainability' for tax calculations.
    """
    __tablename__ = "lot_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("analysis_runs.id"), nullable=True, index=True)
    
    # The transaction that caused the consumption (the Sell/Swap)
    sell_tx_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    sell_tx_external_id = Column(String(255), nullable=True)
    
    # The transaction that provided the cost basis (the Buy/Receive)
    buy_tx_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    buy_tx_external_id = Column(String(255), nullable=True)
    
    asset = Column(String(20), nullable=False, index=True)
    amount = Column(Numeric(precision=20, scale=8), nullable=False)
    
    buy_price = Column(Numeric(precision=12, scale=2), nullable=True)
    sell_price = Column(Numeric(precision=12, scale=2), nullable=True)
    
    cost_basis = Column(Numeric(precision=20, scale=8), nullable=False)
    proceeds = Column(Numeric(precision=20, scale=8), nullable=False)
    gain_loss = Column(Numeric(precision=20, scale=8), nullable=False)
    
    buy_timestamp = Column(DateTime, nullable=False)
    sell_timestamp = Column(DateTime, nullable=False)
    
    holding_period_days = Column(Integer, nullable=True)
    is_long_term = Column(Boolean, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    run = relationship("AnalysisRun")
    sell_tx = relationship("Transaction", foreign_keys=[sell_tx_id])
    buy_tx = relationship("Transaction", foreign_keys=[buy_tx_id])
