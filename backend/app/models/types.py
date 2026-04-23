from __future__ import annotations

from sqlalchemy.types import String, TypeDecorator

from app.core.security import decrypt_secret_if_needed, encrypt_secret_if_needed


class EncryptedString(TypeDecorator[str]):
    """Persist secrets encrypted at rest while exposing plaintext in Python."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return encrypt_secret_if_needed(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return decrypt_secret_if_needed(value)
