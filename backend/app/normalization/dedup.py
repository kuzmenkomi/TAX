from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd


def _row_key(row: pd.Series) -> str:
    # Prefer exchange-provided unique id when present.
    ext = str(row.get("external_id", "") or "").strip()
    if ext:
        return f"external_id:{ext}"

    # Otherwise, build a stable fingerprint from common fields.
    ts = pd.Timestamp(row.get("timestamp"))
    ts_norm = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    parts: list[str] = [
        ts_norm.isoformat(),
        str(row.get("type", "")).upper(),
        str(row.get("asset", "")).upper(),
        str(row.get("amount", "")),
        str(row.get("fee", "")),
        str(row.get("from_wallet", "")),
        str(row.get("to_wallet", "")),
    ]
    raw = "|".join(parts).encode("utf-8", errors="ignore")
    return "fp:" + hashlib.sha256(raw).hexdigest()


def deduplicate_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Remove duplicate transactions (same external_id or same fingerprint).
    Returns (df_deduped, stats).
    """
    if df.empty:
        return df, {"dropped": 0, "kept": 0}

    keys = df.apply(_row_key, axis=1)
    dup_mask = keys.duplicated(keep="first")
    dropped = int(dup_mask.sum())
    kept = int((~dup_mask).sum())
    out = df.loc[~dup_mask].copy()
    return out, {"dropped": dropped, "kept": kept}

