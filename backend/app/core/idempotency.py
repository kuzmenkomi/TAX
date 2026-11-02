"""Idempotency helpers for external side-effects (Stripe, exchanges, tax filings)."""

from __future__ import annotations

import hashlib
import uuid


def make_idempotency_key(*parts: str) -> str:
    """Deterministic idempotency key from logical parts (truncate for Stripe 255 limit)."""
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def random_idempotency_key() -> str:
    return uuid.uuid4().hex
