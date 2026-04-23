from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db import Base


class RestakingEvent(Base):
    __tablename__ = "restaking_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    protocol = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    asset = Column(String(20), nullable=False)
    amount = Column(Numeric(precision=20, scale=8), nullable=False)
    price_usd = Column(Numeric(precision=12, scale=2), nullable=False)
    total_usd = Column(Numeric(precision=14, scale=2), nullable=False)
    tx_hash = Column(String(255), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")


class Layer2Transaction(Base):
    __tablename__ = "l2_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    network = Column(String(50), nullable=False, index=True)
    tx_hash = Column(String(255), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)
    asset = Column(String(20), nullable=False)
    amount = Column(Numeric(precision=20, scale=8), nullable=False)
    price_usd = Column(Numeric(precision=12, scale=2), nullable=False)
    total_usd = Column(Numeric(precision=14, scale=2), nullable=False)
    gas_fee_usd = Column(Numeric(precision=10, scale=2), nullable=True)
    bridge_fee_usd = Column(Numeric(precision=10, scale=2), nullable=True)
    source_network = Column(String(50), nullable=True)
    destination_network = Column(String(50), nullable=True)
    bridge_protocol = Column(String(50), nullable=True)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
