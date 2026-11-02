from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    csv_rel_path = Column(String(1024), nullable=False)
    summary_json = Column(Text, nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 of uploaded file

    user = relationship("User", back_populates="analysis_runs")


class ImportJob(Base):
    __tablename__ = "imports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source = Column(String(64), nullable=False)
    filename = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for duplicate detection
    rows_imported = Column(Integer, nullable=True)             # how many rows were actually saved
    rows_skipped = Column(Integer, nullable=True)              # duplicates skipped
    status = Column(String(32), nullable=False, default="done")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)

    user = relationship("User", back_populates="imports")
