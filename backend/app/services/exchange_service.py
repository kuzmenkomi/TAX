from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import logging

from fastapi import HTTPException, status

from app.core.api_errors import server_error

logger = logging.getLogger(__name__)
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import decrypt_secret_if_needed, encrypt_secret_if_needed
from app.models import AnalysisRun, ExchangeConnection, Portfolio, Transaction, User


def count_exchange_transactions(db: Session, connection: ExchangeConnection) -> int:
    """Count transactions imported for this exchange provider (via analysis run format)."""
    provider = (connection.exchange_name or connection.provider or "").strip().lower()
    if not provider:
        return 0
    return (
        db.query(func.count(Transaction.id))
        .join(AnalysisRun, Transaction.run_id == AnalysisRun.id)
        .filter(
            Transaction.user_id == connection.user_id,
            AnalysisRun.summary_json.ilike(f'%"format": "{provider}"%'),
        )
        .scalar()
        or 0
    )


def _ensure_portfolio(db: Session, user: User) -> Portfolio:
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not portfolio:
        portfolio = Portfolio(
            user_id=user.id,
            country_code="BR",
            name="Principal",
            base_currency="BRL",
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    return portfolio


def connect_exchange(
    db: Session,
    user: User,
    exchange_name: str,
    api_key: str,
    api_secret: str,
    passphrase: Optional[str] = None,
    label: Optional[str] = None,
) -> ExchangeConnection:
    """Validate exchange credentials and store the connection metadata."""
    from app.integrations.exchange_ccxt_adapter import get_exchange_adapter

    try:
        adapter = get_exchange_adapter(
            exchange_name=exchange_name,
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            is_oauth=False, # Manual connection is never OAuth
        )
        adapter.get_balance()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot connect to {exchange_name}: {e}",
        )

    portfolio = _ensure_portfolio(db, user)
    normalized_name = exchange_name.strip().lower()

    conn = ExchangeConnection(
        user_id=user.id,
        portfolio_id=portfolio.id,
        provider=normalized_name,
        exchange_name=normalized_name,
        label=label,
        api_key=encrypt_secret_if_needed(api_key),
        api_secret=encrypt_secret_if_needed(api_secret),
        passphrase=encrypt_secret_if_needed(passphrase),
        has_credentials=True,
        status="connected",
        updated_at=datetime.now(timezone.utc),
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def disconnect_exchange(db: Session, user: User, exchange_id: int) -> None:
    conn = db.query(ExchangeConnection).filter(
        ExchangeConnection.id == exchange_id,
        ExchangeConnection.user_id == user.id,
    ).first()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange not found")
    db.delete(conn)
    db.commit()


def get_user_exchanges(db: Session, user: User) -> list[ExchangeConnection]:
    return (
        db.query(ExchangeConnection)
        .filter(ExchangeConnection.user_id == user.id)
        .all()
    )


def sync_exchange(db: Session, user: User, exchange_id: int) -> dict:
    """Trigger exchange synchronization for the selected connection."""
    conn = db.query(ExchangeConnection).filter(
        ExchangeConnection.id == exchange_id,
        ExchangeConnection.user_id == user.id,
    ).first()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange not found")

    from app.integrations.exchange_ccxt_adapter import fetch_exchange_transactions

    try:
        df = fetch_exchange_transactions(
            exchange_name=conn.exchange_name or conn.provider,
            api_key=decrypt_secret_if_needed(conn.api_key) or "",
            api_secret=decrypt_secret_if_needed(conn.api_secret) or "",
            passphrase=decrypt_secret_if_needed(conn.passphrase),
            is_oauth=conn.is_oauth,
        )
        conn.status = "connected"
        conn.updated_at = datetime.now(timezone.utc)
        conn.last_error = None
        db.commit()

        if not df.empty:
            from app.services.analysis_service import persist_run
            persist_run(
                db=db,
                user_id=user.id,
                normalized=df,
                summary={
                    "format": conn.exchange_name or conn.provider,
                    "exchange_sync": True,
                    "rows_processed": len(df),
                }
            )

        return {
            "exchange_id": exchange_id,
            "exchange": conn.exchange_name or conn.provider,
            "transactions_found": len(df),
            "assets": df["asset"].unique().tolist() if len(df) > 0 else [],
        }
    except Exception as e:
        conn.status = "error"
        conn.last_error = str(e)
        db.commit()
        raise server_error(logger, e, public_message="Could not reach the exchange. Please try again later.")
