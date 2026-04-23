"""
TLH (Tax-Loss Harvesting) + Open Banking ORM Models
SQLAlchemy 2.0 models for complete tax system
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Float, String, Text, DateTime, Numeric, Index, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base

from app.core.db import Base


# ============================================================================
# ENUMS
# ============================================================================

class RecommendationStatus(str, Enum):
    """TLH recommendation statuses"""
    NEW = "new"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    DRY_RUN_PENDING = "dry_run_pending"
    DRY_RUN_COMPLETED = "dry_run_completed"
    PENDING = "pending"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ExecutionStrategy(str, Enum):
    """Execution strategy types"""
    IMMEDIATE = "immediate"
    LIMIT_PRICE = "limit_price"
    SCHEDULED = "scheduled"


class BankType(str, Enum):
    """Supported banks"""
    NUBANK = "nubank"
    MERCADO_PAGO = "mercado_pago"
    LEMON = "lemon"
    BELO = "belo"
    CUSTOM_API = "custom_api"


class BankTransactionType(str, Enum):
    """Bank transaction types"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    FEE = "fee"
    INTEREST = "interest"
    DIVIDEND = "dividend"


class PriceEventType(str, Enum):
    """Price event types"""
    PRICE_DROP = "price_drop"
    LOSS_REALIZED = "loss_realized"
    LIQUIDITY_IMPROVED = "liquidity_improved"
    WASH_SALE_EXPIRED = "wash_sale_expired"
    OPPORTUNITY_EXPIRED = "opportunity_expired"
    MANUAL_TRIGGER = "manual_trigger"


# ============================================================================
# TAX-LOSS HARVESTING MODELS
# ============================================================================

class TLHOpportunity(Base):
    """
    Tax-Loss Harvesting opportunity
    Represents a position that can be harvested for tax benefit
    """
    __tablename__ = "tlh_opportunities"
    __table_args__ = (
        Index("ix_tlh_user_asset", "user_id", "asset"),
        Index("ix_tlh_status", "status"),
        Index("ix_tlh_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    position_id: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Asset details
    asset: Mapped[str] = mapped_column(String(20), nullable=False)  # BTC, ETH, etc.
    loss_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Float, default=24.0)
    
    # Scoring (NOW TRANSPARENT!)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False)
    priority_breakdown: Mapped[dict] = mapped_column(JSON, nullable=True)  # Full breakdown
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(30), default=RecommendationStatus.NEW.value)
    
    # Execution details
    execution_strategy: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    execution_attempts: Mapped[int] = mapped_column(default=0)
    last_execution_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    dry_run_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Order details (after execution)
    order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity_executed: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    average_price_executed: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    fees_paid: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    
    # Wash-sale tracking
    wash_sale_risk: Mapped[bool] = mapped_column(default=False)
    wash_sale_days_remaining: Mapped[int] = mapped_column(default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Notes
    notes: Mapped[str] = mapped_column(Text, default="")
    
    # Relationships
    execution_history: Mapped[list["TLHExecutionHistory"]] = relationship(
        "TLHExecutionHistory",
        back_populates="opportunity",
        cascade="all, delete-orphan"
    )


class TLHExecutionHistory(Base):
    """
    Execution history for each TLH opportunity
    Tracks all execution attempts
    """
    __tablename__ = "tlh_execution_history"
    __table_args__ = (
        Index("ix_exec_opportunity", "opportunity_id"),
        Index("ix_exec_timestamp", "executed_at"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(100), ForeignKey("tlh_opportunities.id"), nullable=False)
    
    # Execution details
    strategy: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, failed, pending, etc.
    
    # Results
    dry_run: Mapped[bool] = mapped_column(default=False)
    order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity_executed: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    average_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    fees_paid: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Full response
    exchange_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationship
    opportunity: Mapped["TLHOpportunity"] = relationship(
        "TLHOpportunity",
        back_populates="execution_history"
    )


# ============================================================================
# OPEN BANKING MODELS
# ============================================================================

class BankAccount(Base):
    """
    Connected bank account
    Stores connection details for LATAM banks (Nubank, Mercado Pago, Lemon, Belo)
    """
    __tablename__ = "bank_accounts"
    __table_args__ = (
        Index("ix_bank_user", "user_id"),
        Index("ix_bank_status", "sync_status"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Bank info
    bank_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "nubank", "mercado_pago", etc.
    account_number: Mapped[str] = mapped_column(String(100), nullable=False)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="BRL")  # BRL, ARS, MXN
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    
    # Credentials (encrypted in production)
    api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_secret: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Sync tracking
    sync_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, syncing, synced, error
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    connected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions: Mapped[list["BankTransaction"]] = relationship(
        "BankTransaction",
        back_populates="account",
        cascade="all, delete-orphan"
    )


class BankTransaction(Base):
    """
    Bank transaction (deposit/withdrawal)
    Fetched from connected bank account
    """
    __tablename__ = "bank_transactions"
    __table_args__ = (
        Index("ix_bank_txn_account", "account_id"),
        Index("ix_bank_txn_date", "date"),
        Index("ix_bank_txn_type", "type"),
        Index("ix_bank_txn_matched", "matched_crypto_transaction_id"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(100), ForeignKey("bank_accounts.id"), nullable=False)
    
    # Transaction details
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # deposit, withdrawal, transfer, etc.
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    counterparty: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Balance after transaction
    balance_after: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    
    # Matching
    matched_crypto_transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    matched_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    account: Mapped["BankAccount"] = relationship(
        "BankAccount",
        back_populates="transactions"
    )


# ============================================================================
# TRANSACTION MATCHING MODELS
# ============================================================================

class TransactionMatch(Base):
    """
    Match between crypto withdrawal and bank deposit
    Links complete crypto → fiat cycle
    """
    __tablename__ = "transaction_matches"
    __table_args__ = (
        Index("ix_match_crypto", "crypto_withdrawal_id"),
        Index("ix_match_bank", "bank_deposit_id"),
        Index("ix_match_confidence", "confidence"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    
    # Links
    crypto_withdrawal_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    bank_deposit_id: Mapped[str] = mapped_column(String(100), ForeignKey("bank_transactions.id"), nullable=False)
    
    # Crypto details
    crypto_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    crypto_currency: Mapped[str] = mapped_column(String(20), nullable=False)  # BTC, ETH, USDC
    
    # Fiat details
    fiat_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    fiat_currency: Mapped[str] = mapped_column(String(10), nullable=False)  # BRL, ARS, MXN
    
    # Conversion
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    fees_paid: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    slippage: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    
    # Timeline
    crypto_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fiat_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    time_delta_hours: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Matching quality
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    match_status: Mapped[str] = mapped_column(String(20), default="matched")
    notes: Mapped[str] = mapped_column(Text, default="")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# PRICE EVENT MODELS
# ============================================================================

class PriceEvent(Base):
    """
    Price events that trigger TLH recalculation
    Tracks: price drops, losses realized, wash-sale expiration, etc.
    """
    __tablename__ = "price_events"
    __table_args__ = (
        Index("ix_event_user", "user_id"),
        Index("ix_event_asset", "asset"),
        Index("ix_event_type", "event_type"),
        Index("ix_event_timestamp", "timestamp"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)  # PRICE_DROP, LOSS_REALIZED, etc.
    asset: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Price details
    previous_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    price_change_pct: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Additional event data
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


# ============================================================================
# AUDIT TRAIL MODEL
# ============================================================================

class TaxAuditTrail(Base):
    """
    Complete audit trail for crypto → fiat → tax compliance
    Documents every step for tax authorities
    """
    __tablename__ = "tax_audit_trail"
    __table_args__ = (
        Index("ix_audit_user", "user_id"),
        Index("ix_audit_timestamp", "timestamp"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Trail details
    transaction_id: Mapped[str] = mapped_column(String(100), nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)  # holdings, exchange, withdrawal, blockchain, bank, matched, tax
    
    # Event
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # purchase, withdrawal, blockchain_confirm, bank_deposit, etc.
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Proof
    proof_hash: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # blockchain TX hash, bank ref, etc.
    proof_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ============================================================================
# CRYPTO WITHDRAWAL MODEL (from exchange)
# ============================================================================

class CryptoWithdrawal(Base):
    """
    Cryptocurrency withdrawal from exchange
    Links to bank deposit via TransactionMatch
    """
    __tablename__ = "crypto_withdrawals"
    __table_args__ = (
        Index("ix_withdrawal_user", "user_id"),
        Index("ix_withdrawal_asset", "asset"),
        Index("ix_withdrawal_date", "date_time"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Withdrawal details
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)  # binance, kraken, coinbase
    asset: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # BTC, ETH, USDC
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    amount_in_usd: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    
    # Blockchain details
    destination_address: Mapped[str] = mapped_column(String(200), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed")  # pending, completed, failed
    
    # Matching
    matched_bank_deposit_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    match_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Timestamps
    date_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
