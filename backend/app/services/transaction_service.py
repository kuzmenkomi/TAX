from __future__ import annotations

import hashlib
import pandas as pd
from sqlalchemy.orm import Session
from app.models import Transaction, User


def _make_external_id(row: pd.Series, run_id: int, idx: int) -> str:
    """Build a stable external_id from row fields if not provided."""
    # Support both lowercase and title-case for keys
    def get_val(key: str):
        return row.get(key.lower()) if key.lower() in row else row.get(key.capitalize())

    ext = str(get_val("external_id") or "").strip()
    if ext:
        return ext
    
    # Fingerprint: timestamp + type + asset + amount
    parts = [
        str(get_val("timestamp") or ""),
        str(get_val("type") or "").upper(),
        str(get_val("asset") or "").upper(),
        str(get_val("amount") or ""),
        str(get_val("fee") or "0"),
    ]
    raw = "|".join(parts).encode("utf-8", errors="ignore")
    return "fp:" + hashlib.sha256(raw).hexdigest()


def save_transactions_from_df(
    db: Session,
    user_id: int,
    run_id: int,
    df: pd.DataFrame,
) -> dict[str, int]:
    """
    Bulk-save transactions from a normalized DataFrame.
    Skips rows whose external_id already exists (deduplication).
    Returns {"imported": N, "skipped": N}.
    """
    if df.empty:
        return {"imported": 0, "skipped": 0}

    # Build the set of external_ids already in DB for this user
    existing_ids: set[str] = set(
        r[0]
        for r in db.query(Transaction.external_id)
        .filter(Transaction.user_id == user_id, Transaction.external_id.isnot(None))
        .all()
    )

    to_insert: list[Transaction] = []
    skipped = 0

    for idx, row in df.iterrows():
        ext_id = _make_external_id(row, run_id, int(str(idx)))

        if ext_id in existing_ids:
            skipped += 1
            continue

        existing_ids.add(ext_id)  # prevent within-batch dups too
        
        amount_val = row.get("amount")
        if pd.isna(amount_val):
            amount_val = row.get("amount_out", 0.0)
            if pd.isna(amount_val):
                amount_val = 0.0
                
        price_val = row.get("price")
        if pd.isna(price_val):
            price_val = None
            
        fee_val = row.get("fee", 0)
        if pd.isna(fee_val):
            fee_val = 0.0

        tx = Transaction(
            user_id=user_id,
            run_id=run_id,
            timestamp=row["timestamp"],
            asset=row["asset"],
            tx_type=row["type"],
            amount=float(amount_val),
            fee=float(fee_val),
            price=float(price_val) if price_val is not None else None,
            total_value=float(row.get("total_value", 0)) if not pd.isna(row.get("total_value")) else 0.0,
            from_wallet=row.get("from_wallet") if not pd.isna(row.get("from_wallet")) else None,
            to_wallet=row.get("to_wallet") if not pd.isna(row.get("to_wallet")) else None,
            external_id=ext_id,
            audit_hash=row.get("audit_hash") if not pd.isna(row.get("audit_hash")) else None,
        )
        to_insert.append(tx)

    if to_insert:
        db.add_all(to_insert)
        db.commit()

    return {"imported": len(to_insert), "skipped": skipped}
