from __future__ import annotations

from sqlalchemy.orm import Session
from app.models import LotMatch, User

def save_lot_matches(db: Session, user: User, run_id: int, matches: list[dict]):
    """
    Persist lot matches to the database for audit and transparency.
    """
    db_matches = []
    for m in matches:
        db_match = LotMatch(
            user_id=user.id,
            run_id=run_id,
            asset=m["asset"],
            amount=m["amount"],
            buy_price=m["buy_price"],
            sell_price=m["sell_price"],
            cost_basis=m["cost_basis"],
            proceeds=m["proceeds"],
            gain_loss=m["gain_loss"],
            buy_timestamp=m["buy_timestamp"],
            sell_timestamp=m["sell_timestamp"],
            sell_tx_id=m["sell_tx_id"],
            sell_tx_external_id=m["sell_tx_external_id"],
            buy_tx_id=m["buy_tx_id"],
            buy_tx_external_id=m["buy_tx_external_id"]
        )
        db_matches.append(db_match)
    
    db.add_all(db_matches)
    db.commit()

def get_matches_for_transaction(db: Session, user_id: int, tx_id: int) -> list[LotMatch]:
    return db.query(LotMatch).filter(
        LotMatch.user_id == user_id,
        LotMatch.sell_tx_id == tx_id
    ).all()

def get_matches_for_run(db: Session, user_id: int, run_id: int) -> list[LotMatch]:
    return db.query(LotMatch).filter(
        LotMatch.user_id == user_id,
        LotMatch.run_id == run_id
    ).all()
