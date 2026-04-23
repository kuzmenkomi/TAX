from __future__ import annotations

from typing import Any

import pandas as pd


def collect_data_issues(
    normalized: pd.DataFrame,
    *,
    dedup_removed: int = 0,
    matches_found: int = 0,
) -> list[dict[str, Any]]:
    """Surface rows that often need user review (MVP)."""
    issues: list[dict[str, Any]] = []

    if normalized is None or normalized.empty:
        issues.append(
            {
                "code": "empty_dataset",
                "severity": "error",
                "message": "No transaction rows after normalization.",
            }
        )
        return issues

    for i, row in normalized.iterrows():
        idx = int(i) if isinstance(i, (int, float)) else i
        try:
            price = float(row.get("price") or 0)
        except (TypeError, ValueError):
            price = 0.0
        if price <= 0:
            asset = str(row.get("asset", "") or "")
            issues.append(
                {
                    "code": "missing_price",
                    "severity": "warning",
                    "row_index": idx,
                    "asset": asset,
                    "type": str(row.get("type", "")),
                    "message": f"Missing or zero spot price for row {idx} ({asset}).",
                }
            )

    try:
        amounts = pd.to_numeric(normalized.get("amount", 0), errors="coerce").fillna(0)
        if (amounts <= 0).any():
            bad = amounts[amounts <= 0].index.tolist()[:20]
            issues.append(
                {
                    "code": "non_positive_amount",
                    "severity": "warning",
                    "row_indices": [int(x) for x in bad],
                    "message": "Some rows have zero or negative amount; verify source data.",
                }
            )
    except Exception:
        pass

    xfer = normalized[normalized["type"].astype(str).str.upper().isin(["TRANSFER", "RECEIVE"])]
    if len(xfer) > 0 and matches_found == 0:
        issues.append(
            {
                "code": "unmatched_transfers",
                "severity": "info",
                "message": "Transfers/receives present but no internal transfer matches; may be cross-wallet or missing counterpart.",
            }
        )

    if dedup_removed > 0:
        issues.append(
            {
                "code": "duplicates_removed",
                "severity": "info",
                "count": dedup_removed,
                "message": f"Deduplication removed {dedup_removed} duplicate row(s).",
            }
        )

    # Negative Balance Detection (running inventory)
    try:
        inventory = {}
        for _, row in normalized.sort_values("timestamp").iterrows():
            asset = str(row["asset"])
            tx_type = str(row["type"]).upper()
            amount = float(row["amount"])
            
            if asset not in inventory:
                inventory[asset] = 0.0
            
            if tx_type in ["BUY", "RECEIVE", "STAKING_REWARD", "FARMING_REWARD", "AIRDROP"]:
                inventory[asset] += amount
            elif tx_type in ["SELL", "TRANSFER"]:
                inventory[asset] -= amount
                
            if inventory[asset] < -1e-8: # small epsilon
                issues.append({
                    "code": "negative_balance",
                    "severity": "error",
                    "asset": asset,
                    "timestamp": str(row["timestamp"]),
                    "message": f"Negative balance detected for {asset}: {-inventory[asset]:.6f} missing. Did you miss an import?"
                })
                # Prevent flood of same error
                inventory[asset] = 0.0 
    except Exception:
        pass

    return issues
