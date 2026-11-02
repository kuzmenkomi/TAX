from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)   # nullable for OAuth-only accounts
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    oauth_provider = Column(String(50), nullable=True)      # "google" | "github" | None
    oauth_provider_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, nullable=False, default=True)
    is_email_verified = Column(Boolean, nullable=False, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    verification_token = Column(String(255), nullable=True, index=True)
    password_reset_token = Column(String(255), nullable=True, index=True)
    password_reset_expires = Column(DateTime, nullable=True)

    # Access control: user | support | admin
    role = Column(String(32), nullable=False, default="user")
    # TOTP 2FA — secret stored encrypted (see app.core.security)
    totp_secret_encrypted = Column(Text, nullable=True)
    totp_pending = Column(Boolean, nullable=False, default=False)
    totp_enabled = Column(Boolean, nullable=False, default=False)
    totp_confirmed_at = Column(DateTime, nullable=True)
    jurisdiction_code = Column(String(2), nullable=False, default="BR", index=True)

    imports = relationship("ImportJob", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")
    analysis_runs = relationship("AnalysisRun", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
