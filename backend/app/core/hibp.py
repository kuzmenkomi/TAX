"""Have I Been Pwned (k-anonymity) password range check."""

from __future__ import annotations

import hashlib
import logging

import httpx

logger = logging.getLogger(__name__)


def password_is_pwned(password: str) -> bool:
    """
    Return True if password SHA-1 suffix appears in HIBP range API.
    On network errors, returns False (fail open) to avoid blocking signups.
    """
    digest = hashlib.sha1(password.encode("utf-8"), usedforsecurity=False).hexdigest().upper()
    prefix, suffix = digest[:5], digest[5:]
    try:
        resp = httpx.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            headers={"Add-Padding": "true"},
            timeout=5.0,
        )
        resp.raise_for_status()
        for line in resp.text.splitlines():
            if ":" not in line:
                continue
            h, _count = line.split(":", 1)
            if h.strip() == suffix:
                return True
    except Exception as e:
        logger.warning("HIBP check failed (non-blocking): %s", e)
    return False
