from __future__ import annotations

from typing import Any

import pandas as pd

from app.config.settings import MatchingConfig


def match_transfers(df: pd.DataFrame, cfg: MatchingConfig) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    transfers = df[df["type"] == "TRANSFER"]
    receives = df[df["type"] == "RECEIVE"]
    used_receive_indices: set[int] = set()

    for transfer_idx, transfer in transfers.iterrows():
        candidates: list[dict[str, Any]] = []
        for receive_idx, receive in receives.iterrows():
            if receive_idx in used_receive_indices:
                continue
            if transfer["asset"] != receive["asset"]:
                continue
            # Some sources don't include fee on transfers (or fee is in another asset).
            # Use best-effort matching: if fee is missing/invalid, assume 0.
            fee_val = transfer.get("fee", 0.0)
            try:
                fee = float(fee_val) if fee_val is not None else 0.0
            except Exception:
                fee = 0.0

            expected_amount = float(transfer["amount"]) - fee
            amount_diff = abs(expected_amount - receive["amount"])
            if amount_diff > cfg.max_amount_diff:
                continue
            time_diff_seconds = abs((transfer["timestamp"] - receive["timestamp"]).total_seconds())
            if time_diff_seconds > cfg.max_time_diff_seconds:
                continue
            confidence = _compute_confidence(transfer, receive, amount_diff)
            explanation = _generate_explanation(transfer, receive, amount_diff, time_diff_seconds, cfg)
            candidates.append(
                {
                    "transfer_index": int(transfer_idx),
                    "receive_index": int(receive_idx),
                    "asset": transfer["asset"],
                    "transfer_amount": float(transfer["amount"]),
                    "receive_amount": float(receive["amount"]),
                    "amount_diff": float(amount_diff),
                    "time_diff_seconds": int(time_diff_seconds),
                    "wallet_match": _wallet_match(transfer, receive),
                    "from_to_match": _from_to_match(transfer, receive),
                    "confidence": round(confidence, 2),
                    "explanation": explanation,
                }
            )
        if candidates:
            best = max(candidates, key=lambda m: m["confidence"])
            used_receive_indices.add(best["receive_index"])
            matches.append(best)

    matches.sort(key=lambda m: m["confidence"], reverse=True)
    return matches


def _wallet_match(transfer: pd.Series, receive: pd.Series) -> bool:
    transfer_to = str(transfer.get("to_wallet", "")).strip()
    receive_to = str(receive.get("to_wallet", "")).strip()
    return bool(transfer_to and receive_to and transfer_to == receive_to)


def _from_to_match(transfer: pd.Series, receive: pd.Series) -> bool:
    t_from = str(transfer.get("from_wallet", "")).strip()
    t_to = str(transfer.get("to_wallet", "")).strip()
    r_from = str(receive.get("from_wallet", "")).strip()
    r_to = str(receive.get("to_wallet", "")).strip()
    if not t_from or not t_to or not r_from or not r_to:
        return False
    return t_from == r_from and t_to == r_to


def _generate_explanation(transfer: pd.Series, receive: pd.Series, amount_diff: float, time_diff: int, cfg: MatchingConfig) -> str:
    reasons = []
    if _wallet_match(transfer, receive):
        reasons.append("Wallets match (same destination)")
    if _from_to_match(transfer, receive):
        reasons.append("Full wallet path matches")
    if amount_diff <= 0.0001:
        reasons.append("Amounts match exactly")
    elif amount_diff <= cfg.max_amount_diff:
        reasons.append(f"Amounts differ by {amount_diff:.6f} (within tolerance)")
    if time_diff <= cfg.max_time_diff_seconds:
        reasons.append(f"Time difference: {time_diff} seconds")
    return "; ".join(reasons) if reasons else "Low confidence match"
