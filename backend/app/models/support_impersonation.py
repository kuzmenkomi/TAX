from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class SupportImpersonationLog(Base):
    """Audit trail when support staff view a customer account (impersonation)."""

    __tablename__ = "support_impersonation_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)
    actor_ip = Column(String(64), nullable=True)

    actor = relationship("User", foreign_keys=[actor_user_id])
    subject = relationship("User", foreign_keys=[subject_user_id])
