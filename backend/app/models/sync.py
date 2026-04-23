from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text

from app.db import Base


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    connection_type = Column(String(32), nullable=False)
    connection_id = Column(Integer, nullable=False)
    job_type = Column(String(64), nullable=True)
    source = Column(String(255), nullable=True)
    status = Column(String(32), nullable=False, default="queued")
    transaction_count = Column(Integer, nullable=True, default=0)
    result = Column(JSON, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True)
