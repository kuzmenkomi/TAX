from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_email_verified
from app.core.db import get_db
from app.models import ExchangeConnection
from app.models import User
from app.schemas.exchange import (
    ExchangeConnectRequest,
    ExchangeConnectionResponse,
    ExchangeListItem,
    ExchangeRegisterRequest,
)
from app.services import exchange_service, billing_service
from app.services.portfolio_service import get_or_create_portfolio

router = APIRouter(tags=["exchange"])


def _serialize_exchange(connection, db: Session | None = None) -> ExchangeConnectionResponse:
    from app.services.exchange_service import count_exchange_transactions

    tx_count = count_exchange_transactions(db, connection) if db is not None else 0

    last_sync = connection.last_synced_at or connection.updated_at
    return ExchangeConnectionResponse(
        id=connection.id,
        exchange_name=connection.exchange_name or connection.provider,
        label=connection.label,
        status=connection.status,
        last_synced=last_sync,
        last_sync_at=last_sync,
        transaction_count=tx_count,
        balance=0.0,  # balance not stored per-connection; future: pull from portfolio
    )


@router.get("/br/exchanges", response_model=list[ExchangeListItem])
def list_supported_exchanges() -> list[ExchangeListItem]:
    from app.integrations.exchange_ccxt_adapter import get_supported_exchanges

    supported = get_supported_exchanges()
    return [
        ExchangeListItem(
            id=item["id"],
            name=item["name"],
            tier=item.get("tier"),
            logo_url=item.get("logo_url"),
        )
        for item in supported
    ]


@router.post("/br/exchange")
def register_exchange(
    body: ExchangeRegisterRequest,
    current_user: User = Depends(require_email_verified),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    billing_service.check_limit(db, current_user.id, "exchanges")
    portfolio = get_or_create_portfolio(db, current_user)
    row = ExchangeConnection(
        user_id=current_user.id,
        portfolio_id=portfolio.id,
        provider=body.provider.strip().lower(),
        label=(body.label or "").strip() or None,
        has_credentials=True,
        status="pending_sync",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "status": row.status, "provider": row.provider}


@router.post("/br/exchange/connect", response_model=ExchangeConnectionResponse)
def connect_exchange(
    body: ExchangeConnectRequest,
    current_user: User = Depends(require_email_verified),
    db: Session = Depends(get_db),
) -> ExchangeConnectionResponse:
    billing_service.check_limit(db, current_user.id, "exchanges")
    connection = exchange_service.connect_exchange(
        db,
        current_user,
        body.exchange_name,
        body.api_key,
        body.api_secret,
        passphrase=body.passphrase,
        label=body.label,
    )
    return _serialize_exchange(connection)


@router.get("/br/exchanges/my", response_model=list[ExchangeConnectionResponse])
def list_my_exchanges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ExchangeConnectionResponse]:
    return [
        _serialize_exchange(connection, db)
        for connection in exchange_service.get_user_exchanges(db, current_user)
    ]


@router.delete("/br/exchange/{exchange_id}")
def disconnect_exchange(
    exchange_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    connection = next(
        (
            row
            for row in exchange_service.get_user_exchanges(db, current_user)
            if row.id == exchange_id
        ),
        None,
    )
    exchange_service.disconnect_exchange(db, current_user, exchange_id)
    return {
        "status": "deleted",
        "exchange": (connection.exchange_name or connection.provider) if connection else str(exchange_id),
    }


@router.post("/br/exchange/{exchange_id}/sync")
def sync_exchange(
    exchange_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return exchange_service.sync_exchange(db, current_user, exchange_id)
