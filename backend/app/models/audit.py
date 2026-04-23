from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("analysis_runs.id"), nullable=True, index=True)
    tx_id = Column(String(255), nullable=True)
    tx_hash = Column(String(255), nullable=True, index=True)
    network = Column(String(50), nullable=False)
    blockchain_proof_url = Column(Text, nullable=True)
    data_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=True)
    timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    analysis_run = relationship("AnalysisRun")
