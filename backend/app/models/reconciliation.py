"""Reconciliation models for tracking and resolving transaction issues."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db import Base


class ReconciliationIssue(Base):
    """Tracks transactions with missing cost basis or unknown sources."""

    __tablename__ = "reconciliation_issues"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("analysis_runs.id"), nullable=False, index=True)

    # Which transaction is affected
    tx_index = Column(Integer, nullable=False)
    tx_hash = Column(String(255), nullable=True)
    asset = Column(String(20), nullable=True)
    amount = Column(Numeric(precision=20, scale=8), nullable=True)
    timestamp = Column(DateTime, nullable=True)

    # Issue classification
    issue_type = Column(
        String(50),
        nullable=False,
        # MISSING_COST_BASIS, UNKNOWN_SOURCE, POSSIBLE_INTERNAL_TRANSFER,
        # POSSIBLE_AIRDROP, DUPLICATE_SUSPECT, ORPHAN_RECEIVE
    )
    severity = Column(String(20), nullable=False, default="warning")  # error, warning, info
    description = Column(Text, nullable=True)

    # Auto-matching suggestions (JSON-encoded list of candidate matches)
    suggested_matches_json = Column(Text, nullable=True)

    # Resolution
    resolved = Column(Boolean, nullable=False, default=False, index=True)
    resolved_as = Column(
        String(50),
        nullable=True,
        # PURCHASE, GIFT, AIRDROP, INTERNAL_TRANSFER, MINING, STAKING_REWARD, IGNORE
    )
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_user = Column(Boolean, nullable=True)  # True = manual, False = auto

    # Overrides applied upon resolution
    cost_basis_override = Column(Numeric(precision=14, scale=2), nullable=True)
    linked_wallet = Column(String(255), nullable=True)  # If resolved as internal transfer
    linked_tx_index = Column(Integer, nullable=True)  # Matched transaction index

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User")
    analysis_run = relationship("AnalysisRun")
