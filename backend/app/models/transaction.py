from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("analysis_runs.id"), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    asset = Column(String(20), nullable=False, index=True)
    tx_type = Column(String(50), nullable=False)
    amount = Column(Numeric(precision=20, scale=8), nullable=False)
    fee = Column(Numeric(precision=20, scale=8), nullable=True, default=Decimal("0"))
    price = Column(Numeric(precision=12, scale=2), nullable=True)
    total_value = Column(Numeric(precision=14, scale=2), nullable=False)
    from_wallet = Column(String(255), nullable=True)
    to_wallet = Column(String(255), nullable=True)
    external_id = Column(String(255), nullable=True, unique=True)
    audit_hash = Column(String(64), nullable=True)
    block_number = Column(BigInteger(), nullable=True)
    proof_url = Column(Text, nullable=True)
    custom_tag = Column(String(64), nullable=True)  # User override: "gift", "personal", "lost", "stolen", etc.
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    analysis_run = relationship("AnalysisRun")
