"""Security utilities - unified from existing implementations."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from jose import jwt

from app.core.config import get_settings

MAX_PASSWORD_BYTES = 72


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes")
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode()


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload["exp"] = expire
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _get_multi_fernet() -> MultiFernet:
    settings = get_settings()
    keys = settings.all_encryption_keys
    if not keys:
        raise ValueError("At least one ENCRYPTION_KEY is required.")
    
    # Fernet requires keys to be base64-encoded 32-byte strings.
    fernet_instances = [Fernet(k.encode()) for k in keys]
    return MultiFernet(fernet_instances)


def encrypt_secret(plaintext: str) -> str:
    """Encrypt using the primary (first) key in the rotation list."""
    return _get_multi_fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    """Try to decrypt using all keys in the rotation list."""
    return _get_multi_fernet().decrypt(ciphertext.encode()).decode()


def is_encrypted_secret(value: str | None) -> bool:
    if not value:
        return False
    try:
        decrypt_secret(value)
        return True
    except (InvalidToken, ValueError, TypeError):
        return False


def encrypt_secret_if_needed(value: str | None) -> str | None:
    if not value:
        return None
    return value if is_encrypted_secret(value) else encrypt_secret(value)


def decrypt_secret_if_needed(value: str | None) -> str | None:
    if not value:
        return None
    return decrypt_secret(value) if is_encrypted_secret(value) else value
