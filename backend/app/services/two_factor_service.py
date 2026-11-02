"""Business logic for optional TOTP 2FA — isolated from routers and models."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decrypt_secret_if_needed, encrypt_secret_if_needed, verify_password
from app.models import User
from app.security.totp import generate_secret, provisioning_uri, verify_totp

logger = logging.getLogger(__name__)


def begin_totp_setup(db: Session, user: User, *, issuer: str) -> tuple[str, str]:
    if user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is already enabled")
    secret = generate_secret()
    user.totp_secret_encrypted = encrypt_secret_if_needed(secret)
    user.totp_pending = True
    user.totp_enabled = False
    db.commit()
    db.refresh(user)
    uri = provisioning_uri(secret=secret, account_email=user.email, issuer=issuer)
    logger.info("2FA setup started for user_id=%s", user.id)
    return secret, uri


def confirm_totp_setup(db: Session, user: User, code: str) -> None:
    if not user.totp_pending or not user.totp_secret_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending 2FA setup. Start setup first.",
        )
    secret = decrypt_secret_if_needed(user.totp_secret_encrypted)
    if not verify_totp(secret, code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authenticator code")
    user.totp_enabled = True
    user.totp_pending = False
    user.totp_confirmed_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("2FA enabled for user_id=%s", user.id)


def cancel_totp_setup(db: Session, user: User) -> None:
    if user.totp_enabled:
        return
    user.totp_secret_encrypted = None
    user.totp_pending = False
    db.commit()


def disable_totp(db: Session, user: User, password: str, code: str) -> None:
    if not user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is not enabled")
    if not user.hashed_password or not verify_password(password, str(user.hashed_password)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password")
    secret = decrypt_secret_if_needed(user.totp_secret_encrypted or "")
    if not secret or not verify_totp(secret, code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authenticator code")
    user.totp_secret_encrypted = None
    user.totp_enabled = False
    user.totp_pending = False
    user.totp_confirmed_at = None
    db.commit()
    logger.info("2FA disabled for user_id=%s", user.id)


def verify_user_totp_code(user: User, code: str) -> bool:
    if not user.totp_enabled or not user.totp_secret_encrypted:
        return False
    secret = decrypt_secret_if_needed(user.totp_secret_encrypted)
    return bool(secret and verify_totp(secret, code))
