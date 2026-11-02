from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, Request, status
import jwt
from jwt import PyJWTError as JWTError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.cookies import ACCESS_COOKIE
from app.core.db import get_db
from app.core.security import hash_password, verify_password
from app.models import User

logger = logging.getLogger(__name__)

# Simple in-memory revocation set (use Redis in production)
_revoked_tokens: set[str] = set()


def get_password_hash(password: str) -> str:
    return hash_password(password)


def get_access_token(request: Request) -> str | None:
    """Bearer token from Authorization header, or httpOnly access cookie."""
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        t = auth[7:].strip()
        if t:
            return t
    return request.cookies.get(ACCESS_COOKIE)


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=7)
    )
    to_encode.update({"exp": expire, "refresh": True})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, str(user.hashed_password)):
        return None
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = get_access_token(request)
    if not token:
        raise credentials_exception

    if token in _revoked_tokens:
        raise credentials_exception

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("tfa_pending") is True:
            raise credentials_exception
        email: str | None = payload.get("sub")  # type: ignore[assignment]
        if email is None:
            raise credentials_exception

        is_impersonation = payload.get("imp") is True
        actor_email: str | None = payload.get("act")
        log_id = payload.get("sid")

        if is_impersonation:
            if not actor_email or log_id is None:
                raise credentials_exception
            from app.models.support_impersonation import SupportImpersonationLog

            log = (
                db.query(SupportImpersonationLog)
                .filter(
                    SupportImpersonationLog.id == int(log_id),
                    SupportImpersonationLog.ended_at.is_(None),
                )
                .first()
            )
            if not log:
                raise credentials_exception
            user = get_user_by_email(db, email=email)
            if user is None or not user.is_active:
                raise credentials_exception
            if user.id != log.subject_user_id:
                raise credentials_exception
            request.state.impersonation = {
                "log_id": log.id,
                "actor_email": str(actor_email),
                "subject_email": user.email,
            }
            return user

    except JWTError as exc:
        raise credentials_exception from exc

    user = get_user_by_email(db, email=email)
    if user is None or not user.is_active:
        raise credentials_exception

    return user


def verify_tfa_pending_token(token: str) -> str:
    """Validate short-lived JWT issued after password/OAuth when 2FA is required."""
    settings = get_settings()
    bad = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired 2FA token",
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise bad from exc
    if payload.get("tfa_pending") is not True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type",
        )
    email = payload.get("sub")
    if not email:
        raise bad
    return str(email)


def require_not_impersonating(request: Request, user: User = Depends(get_current_user)) -> User:
    """Block account-changing actions while support is viewing this session."""
    if getattr(request.state, "impersonation", None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action is not allowed while viewing a customer account.",
        )
    return user


def require_email_verified(current_user: User = Depends(get_current_user)) -> User:
    """Require verified email for sensitive operations (exchange keys, exports, etc.)."""
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before using this feature.",
        )
    return current_user
