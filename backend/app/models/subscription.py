from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # Stripe identifiers
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, index=True)
    
    # Plan details
    # Options: "free", "pro", "business"
    plan = Column(String(32), nullable=False, default="free")
    
    # Status: "active", "canceled", "incomplete", "past_due", "unpaid"
    status = Column(String(32), nullable=False, default="active")
    
    current_period_end = Column(DateTime, nullable=True)
    
    # Usage tracking (optional, but good for gating)
    transaction_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="subscription_info")
