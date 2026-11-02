from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User


def register_user(db: Session, email: str, password: str) -> tuple[User, str]:
    """Создаёт пользователя, возвращает (user, verification_token)."""
    from app.core.config import get_settings
    from app.core.hibp import password_is_pwned

    email = email.strip().lower()

    settings = get_settings()
    if settings.is_production or settings.APP_ENV == "staging":
        if password_is_pwned(password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This password appears in known data breaches. Please choose another.",
            )

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    verification_token = str(uuid.uuid4())
    user = User(
        email=email,
        hashed_password=hash_password(password),
        verification_token=verification_token,
        is_email_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, verification_token


def login_or_register_via_oauth(
    db: Session,
    provider: str,
    provider_id: str,
    email: str,
    name: str | None = None,
    avatar_url: str | None = None,
    *,
    apply_geo: bool = False,
    request=None,
) -> User:
    """Find or create a user via social OAuth (Google / GitHub).

    Logic:
    1. Look up by provider + provider_id  → returning social user → update & return
    2. Look up by email                   → existing password user → link OAuth & return
    3. Neither found                      → auto-register (email already verified by provider)
    """
    email = email.strip().lower()

    # Case 1: returning OAuth user
    user = (
        db.query(User)
        .filter(User.oauth_provider == provider, User.oauth_provider_id == str(provider_id))
        .first()
    )
    if user:
        # Refresh profile data
        if name:
            user.full_name = name
        if avatar_url:
            user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
        return user

    # Case 2: email already in system (registered via password)
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Link the OAuth account
        user.oauth_provider    = provider
        user.oauth_provider_id = str(provider_id)
        user.is_email_verified = True
        if name and not user.full_name:
            user.full_name = name
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
        logger.info("Audit log: Linked %s OAuth to existing account %s", provider, email)
        return user

    # Case 3: brand new user — email verified by provider, no password needed
    user = User(
        email=email,
        hashed_password=None,
        full_name=name,
        avatar_url=avatar_url,
        oauth_provider=provider,
        oauth_provider_id=str(provider_id),
        is_email_verified=True,
        email_verified_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    if apply_geo and request is not None:
        from app.services.jurisdiction_geo_service import apply_registration_geo

        apply_registration_geo(db, user, request)
    logger.info("Audit log: Auto-registered new user %s via %s OAuth", email, provider)
    return user


def login_user(db: Session, email: str, password: str) -> str:
    """Аутентифицирует пользователя, возвращает JWT access token."""
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    return create_access_token({"sub": user.email})


def verify_email(db: Session, token: str) -> User:
    """Подтверждает email по токену из письма."""
    user = db.query(User).filter(User.verification_token == token.strip()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    user.is_email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    user.verification_token = None
    db.commit()
    return user


def request_password_reset(db: Session, email: str) -> str | None:
    """Генерирует reset-токен. Возвращает токен или None если пользователь не найден.
    Caller не должен раскрывать факт существования email."""
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None

    reset_token = str(uuid.uuid4())
    user.password_reset_token = reset_token
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()
    return reset_token


def confirm_password_reset(db: Session, token: str, new_password: str) -> None:
    """Применяет новый пароль по reset-токену."""
    user = db.query(User).filter(User.password_reset_token == token.strip()).first()
    if (
        not user
        or not user.password_reset_expires
        or user.password_reset_expires < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    user.hashed_password = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()


def save_refresh_token(db: Session, user_id: int, token: str, expires_at: datetime, revoke_others: bool = False) -> None:
    """Saves a refresh token to the database."""
    from app.models import RefreshToken
    
    if revoke_others:
        db.query(RefreshToken).filter(RefreshToken.user_id == user_id).update({"revoked": True})
    
    db_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()


def verify_refresh_token(db: Session, token: str) -> User:
    """
    Verifies a refresh token and returns the user.
    Implements Token Rotation Reuse Detection:
    If a revoked token is used, it signals a potential compromise, 
    and all active tokens for the user are invalidated.
    """
    from jose import jwt, JWTError
    from app.core.config import get_settings
    from app.models import RefreshToken, User
    
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if not payload.get("refresh"):
            raise ValueError("Not a refresh token")
        email = payload.get("sub")
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    # Check DB for the token
    db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    
    if not db_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found")
        
    if db_token.revoked:
        # Reuse detected! Potential compromise.
        # Revoke ALL active tokens for this user as a security measure.
        db.query(RefreshToken).filter(RefreshToken.user_id == db_token.user_id).update({"revoked": True})
        db.commit()
        logger.warning(f"SECURITY ALERT: Refresh token reuse detected for user_id {db_token.user_id}. All tokens revoked.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Security breach detected. Please login again.")
        
    if db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        
    # Mark the consumed token as revoked (rotation)
    db_token.revoked = True
    db.commit()
    
    return user


def delete_user_data(db: Session, user_id: int) -> None:
    """
    Cascading delete of all user data for LGPD/GDPR compliance.
    Removes user, transactions, exchange connections, wallets, and analysis runs.
    """
    from app.models import (
        User, Transaction, ExchangeConnection, WalletConnection, 
        AnalysisRun, UserTaxProfile, RefreshToken, Portfolio
    )
    
    # 1. Delete dependent data
    db.query(Transaction).filter(Transaction.user_id == user_id).delete()
    db.query(ExchangeConnection).filter(ExchangeConnection.user_id == user_id).delete()
    db.query(WalletConnection).filter(WalletConnection.user_id == user_id).delete()
    db.query(AnalysisRun).filter(AnalysisRun.user_id == user_id).delete()
    db.query(UserTaxProfile).filter(UserTaxProfile.user_id == user_id).delete()
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
    db.query(Portfolio).filter(Portfolio.user_id == user_id).delete()
    
    # 2. Delete the user itself
    db.query(User).filter(User.id == user_id).delete()
    
    db.commit()
