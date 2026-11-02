"""
Tamper-evident audit chain (skeleton).

Production: persist each entry with prev_hash + entry_hash and periodic Merkle anchoring.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_prev_chain_tip: str | None = None


def append_audit_event(event_type: str, payload: dict[str, Any]) -> str:
    """Compute chained hash for an event; logs structured record (DB persistence TODO)."""
    global _prev_chain_tip
    body = json.dumps(
        {"ts": datetime.now(timezone.utc).isoformat(), "type": event_type, "data": payload},
        sort_keys=True,
        default=str,
    )
    material = f"{_prev_chain_tip or 'genesis'}|{body}"
    tip = hashlib.sha256(material.encode()).hexdigest()
    _prev_chain_tip = tip
    logger.info("audit_chain tip=%s type=%s", tip[:16], event_type)
    return tip
