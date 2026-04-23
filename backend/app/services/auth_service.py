from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User


def register_user(db: Session, email: str, password: str) -> tuple[User, str]:
    """Создаёт пользователя, возвращает (user, verification_token)."""
    email = email.strip().lower()

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
