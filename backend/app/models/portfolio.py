from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base

from .types import EncryptedString


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    country_code = Column(String(2), nullable=False, default="BR")
    name = Column(String(128), nullable=False, default="Principal")
    base_currency = Column(String(8), nullable=False, default="BRL")
    tax_structure = Column(String(32), nullable=True)
    portfolio_size = Column(String(32), nullable=True)
    is_onboarded = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="portfolios")
    exchange_connections = relationship("ExchangeConnection", back_populates="portfolio")
    wallet_connections = relationship("WalletConnection", back_populates="portfolio")


class ExchangeConnection(Base):
    __tablename__ = "exchange_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    exchange_name = Column(String(64), nullable=True)
    api_key = Column(EncryptedString(512), nullable=True)
    api_secret = Column(EncryptedString(512), nullable=True)
    passphrase = Column(EncryptedString(512), nullable=True)
    label = Column(String(128), nullable=True)
    has_credentials = Column(Boolean, nullable=False, default=False)
    status = Column(String(32), nullable=False, default="pending")
    sync_status = Column(String(32), nullable=False, default="idle")
    auto_sync_enabled = Column(Boolean, nullable=False, default=True)
    sync_interval_hours = Column(Integer, nullable=False, default=4)
    last_synced_at = Column(DateTime, nullable=True)
    next_sync_at = Column(DateTime, nullable=True)
    is_oauth = Column(Boolean, nullable=False, default=False)
    oauth_expires_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True)

    portfolio = relationship("Portfolio", back_populates="exchange_connections")


class WalletConnection(Base):
    __tablename__ = "wallet_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    chain = Column(String(32), nullable=False)
    address = Column(String(512), nullable=False)
    label = Column(String(128), nullable=True)
    sync_status = Column(String(32), nullable=False, default="idle")
    auto_sync_enabled = Column(Boolean, nullable=False, default=True)
    sync_interval_hours = Column(Integer, nullable=False, default=6)
    last_synced_at = Column(DateTime, nullable=True)
    next_sync_at = Column(DateTime, nullable=True)
    last_block_synced = Column(String(128), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True)

    portfolio = relationship("Portfolio", back_populates="wallet_connections")
