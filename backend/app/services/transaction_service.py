from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session
from app.models import Transaction, User

def save_transactions_from_df(db: Session, user_id: int, run_id: int, df: pd.DataFrame) -> list[Transaction]:
    """
    Bulk save transactions from a normalized DataFrame.
    Returns the list of saved Transaction objects (with IDs).
    """
    transactions = []
    for idx, row in df.iterrows():
        tx = Transaction(
            user_id=user_id,
            run_id=run_id,
            timestamp=row["timestamp"],
            asset=row["asset"],
            tx_type=row["type"],
            amount=row["amount"],
            fee=row.get("fee", 0),
            price=row.get("price"),
            total_value=row.get("total_value", 0),
            from_wallet=row.get("from_wallet"),
            to_wallet=row.get("to_wallet"),
            external_id=row.get("external_id") or f"run_{run_id}_{idx}",
            audit_hash=row.get("audit_hash"),
        )
        transactions.append(tx)
    
    db.add_all(transactions)
    db.commit()
    for tx in transactions:
        db.refresh(tx)
    return transactions
