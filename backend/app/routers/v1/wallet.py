from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.db import get_db
from app.models import AnalysisRun, ExchangeConnection, User, WalletConnection
from app.schemas.wallet import BlockchainImportRequest, WalletConnectRequest, WalletResponse
from app.services.transaction_categories import classify_transaction_category
from app.services import wallet_service, billing_service

router = APIRouter(tags=["wallet"])


@router.post("/br/wallet", response_model=WalletResponse)
def connect_wallet(
    body: WalletConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WalletResponse:
    billing_service.check_limit(db, current_user.id, "wallets")
    wallet = wallet_service.create_wallet(db, current_user, body.chain, body.address, body.label)
    return WalletResponse.model_validate(wallet)


@router.post("/br/wallet/import-blockchain")
def import_blockchain_wallet(
    body: BlockchainImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    billing_service.check_limit(db, current_user.id, "wallets")
    return wallet_service.import_blockchain_wallet(
        db,
        current_user,
        body.chain,
        body.address,
        body.label,
    )


@router.get("/br/connections")
def list_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, object]]]:
    return wallet_service.list_connections(db, current_user)


@router.post("/br/wallet/{wallet_id}/sync")
def sync_wallet(
    wallet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    from app.scheduler import manual_sync_wallet

    wallet = db.query(WalletConnection).filter(
        WalletConnection.id == wallet_id,
        WalletConnection.user_id == current_user.id,
    ).first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    result = manual_sync_wallet(wallet_id)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return result


@router.delete("/br/wallet/{wallet_id}")
def delete_wallet(
    wallet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    wallet = wallet_service.delete_wallet(db, current_user, wallet_id)
    return {
        "status": "deleted",
        "wallet_id": wallet_id,
        "wallet": wallet.label or wallet.address,
    }


def _parse_wallet_id(from_wallet: str | None) -> int | None:
    if not from_wallet:
        return None
    try:
        return int(str(from_wallet).strip())
    except ValueError:
        return None


def _load_run_formats(db: Session, run_ids: set[int]) -> dict[int, str]:
    if not run_ids:
        return {}
    rows = db.query(AnalysisRun).filter(AnalysisRun.id.in_(run_ids)).all()
    formats: dict[int, str] = {}
    for run in rows:
        try:
            summary = json.loads(run.summary_json or "{}")
        except json.JSONDecodeError:
            summary = {}
        formats[run.id] = str(summary.get("format", "")).strip().lower()
    return formats


def _load_wallet_chains(db: Session, user_id: int, wallet_ids: set[int]) -> dict[int, str]:
    if not wallet_ids:
        return {}
    rows = (
        db.query(WalletConnection)
        .filter(
            WalletConnection.user_id == user_id,
            WalletConnection.id.in_(wallet_ids),
        )
        .all()
    )
    return {row.id: row.chain for row in rows}


def _match_connection_id(
    import_format: str,
    exchanges: list[ExchangeConnection],
) -> int | None:
    if not import_format or import_format in {"native", "csv"}:
        return None
    for connection in exchanges:
        provider = (connection.exchange_name or connection.provider or "").strip().lower()
        if provider and (provider == import_format or provider in import_format or import_format in provider):
            return connection.id
    return None


@router.get("/br/wallet/transactions")
def list_wallet_transactions(
    wallet_id: int | None = None,
    run_id: int | None = None,
    category: str | None = None,
    limit: int = 10000,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    from app.models.transaction import Transaction
    from app.models.accounting import LotMatch

    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if wallet_id:
        query = query.filter(Transaction.from_wallet == str(wallet_id))
    if run_id:
        query = query.filter(Transaction.run_id == run_id)

    txs = query.order_by(Transaction.timestamp.desc()).all()

    normalized_category = str(category or "").strip().upper() or None
    if normalized_category:
        allowed_categories = {"TRADE", "TRANSFER", "INCOME", "OTHER"}
        if normalized_category not in allowed_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported transaction category: {normalized_category}",
            )
        txs = [
            tx for tx in txs
            if classify_transaction_category(tx.tx_type, custom_tag=tx.custom_tag) == normalized_category
        ]

    txs = txs[offset: offset + limit]

    run_ids = {tx.run_id for tx in txs if tx.run_id}
    run_formats = _load_run_formats(db, run_ids)
    wallet_ids = {_parse_wallet_id(tx.from_wallet) for tx in txs}
    wallet_ids.discard(None)
    wallet_chains = _load_wallet_chains(db, current_user.id, {wid for wid in wallet_ids if wid is not None})
    exchanges = (
        db.query(ExchangeConnection)
        .filter(ExchangeConnection.user_id == current_user.id)
        .all()
    )

    # Load lot match gain/loss for all sell transactions in one query
    sell_tx_ids = [tx.id for tx in txs if str(tx.tx_type or "").upper() in ("SELL", "OUT", "WITHDRAW")]
    lot_match_gain: dict[int, float] = {}
    if sell_tx_ids:
        matches = (
            db.query(LotMatch.sell_tx_id, LotMatch.gain_loss)
            .filter(
                LotMatch.user_id == current_user.id,
                LotMatch.sell_tx_id.in_(sell_tx_ids),
            )
            .all()
        )
        for m in matches:
            lot_match_gain[m.sell_tx_id] = lot_match_gain.get(m.sell_tx_id, 0.0) + float(m.gain_loss or 0)

    # Income-type transaction types
    _INCOME_TYPES = frozenset({
        "STAKING_REWARD", "AIRDROP", "LENDING_INTEREST", "MINING",
        "FARMING_REWARD", "INTEREST", "STAKING", "LENDING",
    })

    payload: list[dict[str, object]] = []
    for tx in txs:
        resolved_wallet_id = _parse_wallet_id(tx.from_wallet)
        import_format = run_formats.get(tx.run_id, "") if tx.run_id else ""
        is_onchain = import_format.startswith("onchain:")
        if resolved_wallet_id is not None:
            source_kind = "wallet"
            source_method = "wallet"
            blockchain = wallet_chains.get(resolved_wallet_id, tx.from_wallet or "Wallet")
        elif tx.run_id and not is_onchain:
            source_kind = "csv"
            source_method = "csv"
            blockchain = import_format or "CSV"
        else:
            source_kind = "wallet" if is_onchain else "csv"
            source_method = "wallet" if is_onchain else "csv"
            blockchain = (
                import_format.split(":", 1)[1] if is_onchain and ":" in import_format else (tx.from_wallet or "CSV")
            )

        tx_type_upper = str(tx.tx_type or "").upper()
        gross_value = float(tx.total_value) if tx.total_value else float(tx.price or 0) * float(tx.amount)

        # Compute realized_gain_usd:
        # - For disposals (SELL/OUT/WITHDRAW): use lot match gain/loss from DB (net of cost basis).
        # - For income events: recognized at FMV (full value is the income).
        # - For buys and transfers: 0 (no realized gain).
        if tx_type_upper in ("SELL", "OUT", "WITHDRAW"):
            realized_gain_usd = lot_match_gain.get(tx.id, None)
            # If no lot match stored yet (e.g. old run), fall back to None so frontend uses its own calc
        elif tx_type_upper in _INCOME_TYPES:
            realized_gain_usd = gross_value  # FMV at receipt = taxable income
        else:
            realized_gain_usd = None  # BUY, TRANSFER, etc. — not a realized gain

        connection_id = _match_connection_id(import_format, exchanges)
        payload.append(
            {
                "id": tx.id,
                "hash": tx.external_id or str(tx.id),
                "blockchain": blockchain,
                "token": tx.asset,
                "amount": float(tx.amount),
                "value_usd": gross_value,
                "realized_gain_usd": realized_gain_usd,
                "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
                "type": tx.tx_type,
                "category": classify_transaction_category(tx.tx_type, custom_tag=tx.custom_tag),
                "status": "completed",
                "source": source_kind,
                "source_method": source_method,
                "import_format": import_format,
                "run_id": tx.run_id,
                "wallet_id": resolved_wallet_id,
                "connection_id": connection_id,
                "fee": float(tx.fee or 0),
            }
        )
    return payload
