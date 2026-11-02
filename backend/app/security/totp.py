"""TOTP (RFC 6238) helpers — keep crypto/OTP logic separate from HTTP and persistence."""
from __future__ import annotations

import pyotp

DEFAULT_ISSUER = "Declairo"


def generate_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(*, secret: str, account_email: str, issuer: str = DEFAULT_ISSUER) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=account_email, issuer_name=issuer)


def verify_totp(secret: str, code: str, *, valid_window: int = 1) -> bool:
    """valid_window: accept drift of ±N 30-second steps."""
    cleaned = (code or "").strip().replace(" ", "")
    if not cleaned.isdigit() or len(cleaned) not in (6, 8):
        return False
    return bool(pyotp.TOTP(secret).verify(cleaned, valid_window=valid_window))
