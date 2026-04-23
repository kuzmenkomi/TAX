from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.db import get_db
from app.integrations.exchange_ccxt import fetch_exchange_spot_trades_dataframe
from app.integrations.explorer_fetch import fetch_evm_transfers, fetch_solana_transfers
from app.models import ImportJob, SyncJob, User, WalletConnection
from app.schemas.sync import (
    BrBinanceSyncIn,
    BrSyncIn,
    BrWalletOnchainIn,
    SyncEnqueueResponse,
    SyncExchangeIn,
    SyncJobInfo,
    SyncStatusResponse,
    SyncWalletIn,
)
from app.services.analysis_service import analyze_from_dataframe, persist_run
from app.tax.capabilities import list_countries

router = APIRouter(tags=["sync"])


def _pipeline_response(
    db: Session,
    current_user: User,
    result: dict,
    *,
    filenames: str,
    format_name: str,
    quote_currency: str,
    accounting_method: str,
    use_ptax: bool,
) -> dict[str, object]:
    run_id = persist_run(
        db,
        current_user.id,
        result["normalized"],
        {
            "issues": result["issues"],
            "pnl": result["pnl"],
            "matches_sample": result["matches"][:20],
            "filenames": filenames,
            "format": format_name,
            "quote_currency": quote_currency,
            "accounting_method": accounting_method,
            "use_ptax": bool(use_ptax),
        },
    )
    return {
        "status": "ok",
        "filename": filenames,
        "rows_processed": result["rows_processed"],
        "matches_found": result["matches_found"],
        "matches": result["matches"][:50],
        "dedup": result["dedup"],
        "pnl": result["pnl"],
        "issues": result["issues"],
        "analysis_run_id": run_id,
        "quote_currency": quote_currency.upper(),
        "use_ptax": bool(use_ptax),
        "income_events": result.get("income_events", {}),
        "loss_harvesting": result.get("loss_harvesting", {}),
        "monthly_sales_brl": result.get("monthly_sales_brl", {}),
        "isencao_threshold_brl": result.get("isencao_threshold_brl", 35000.0),
        "darf": result.get("darf"),
        "offshore_onshore": result.get("offshore_onshore", {}),
        "tax_savings_opportunities": result.get("tax_savings_opportunities", []),
        "p2p_self_custody_count": result.get("p2p_self_custody_count", 0),
    }


def _analyze_wallet_fetch(
    chain: str,
    address: str,
    etherscan_api_key: str | None = None,
    polygonscan_api_key: str | None = None,
):
    normalized = chain.strip().lower()
    try:
        if normalized in {"ethereum", "eth"}:
            return fetch_evm_transfers(address, "ethereum", etherscan_api_key)
        if normalized in {"polygon", "matic"}:
            return fetch_evm_transfers(address, "polygon", polygonscan_api_key)
        if normalized in {"solana", "sol"}:
            return fetch_solana_transfers(address)
        raise HTTPException(status_code=400, detail="Unsupported chain. Use ethereum/polygon/solana.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"On-chain fetch failed: {exc}") from exc


@router.get("/br/sync/status", response_model=SyncStatusResponse)
def sync_status(current_user: User = Depends(get_current_user)) -> SyncStatusResponse:
    from app.scheduler import get_sync_status

    return get_sync_status()


@router.post("/br/sync/wallets")
def sync_all_wallets_endpoint(current_user: User = Depends(get_current_user)) -> dict[str, object]:
    from app.scheduler import sync_all_wallets

    return sync_all_wallets()


@router.post("/br/sync/prices")
def update_prices_endpoint(current_user: User = Depends(get_current_user)) -> dict[str, object]:
    from app.scheduler import update_prices

    return update_prices()


@router.post("/br/sync/exchanges")
def sync_all_exchanges_endpoint(current_user: User = Depends(get_current_user)) -> dict[str, object]:
    from app.scheduler import sync_all_exchanges

    return sync_all_exchanges()


@router.post("/br/sync/enqueue", response_model=SyncEnqueueResponse)
def enqueue_sync(
    body: BrSyncIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SyncEnqueueResponse:
    connection_type = body.connection_type.strip().lower()
    if connection_type not in {"exchange", "wallet"}:
        raise HTTPException(status_code=400, detail="connection_type must be exchange or wallet")

    job = SyncJob(
        user_id=current_user.id,
        connection_type=connection_type,
        connection_id=body.connection_id,
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return SyncEnqueueResponse(job_id=job.id, status=job.status)


@router.get("/capabilities")
def capabilities() -> dict[str, object]:
    return {"countries": list_countries()}


@router.post("/br/binance/sync-analyze")
def binance_sync_analyze(
    body: BrBinanceSyncIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        raw = fetch_exchange_spot_trades_dataframe(
            body.provider,
            body.api_key,
            body.api_secret,
            symbols=body.symbols,
            limit_per_symbol=body.limit_per_symbol,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if raw is None or raw.empty:
        raise HTTPException(status_code=400, detail="No trades returned from exchange.")

    result = analyze_from_dataframe(
        raw,
        format_name="native",
        accounting_method=body.accounting_method,
        country=body.country,
        quote_currency=body.quote_currency,
        use_ptax=body.use_ptax,
        max_amount_diff=body.max_amount_diff,
        max_time_diff_seconds=body.max_time_diff_seconds,
    )
    db.add(ImportJob(user_id=current_user.id, source="binance_api", filename="binance_api", status="done"))
    db.commit()
    return _pipeline_response(
        db,
        current_user,
        result,
        filenames="binance_api",
        format_name="binance_api",
        quote_currency=body.quote_currency,
        accounting_method=body.accounting_method,
        use_ptax=body.use_ptax,
    )


@router.post("/sync-exchange")
def sync_exchange_endpoint(
    body: SyncExchangeIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        raw = fetch_exchange_spot_trades_dataframe(
            body.provider,
            body.api_key,
            body.api_secret,
            symbols=body.symbols,
            limit_per_symbol=body.limit_per_symbol,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if raw is None or raw.empty:
        raise HTTPException(status_code=400, detail="No trades returned from exchange. Verify API credentials and symbol list.")

    result = analyze_from_dataframe(
        raw,
        format_name="native",
        accounting_method=body.accounting_method,
        country=body.country,
        quote_currency=body.quote_currency,
        use_ptax=body.use_ptax,
        max_amount_diff=0.01,
        max_time_diff_seconds=3600,
    )
    db.add(ImportJob(user_id=current_user.id, source=f"sync:{body.provider}", filename=f"{body.provider}_api", status="done"))
    db.commit()
    return _pipeline_response(
        db,
        current_user,
        result,
        filenames=f"{body.provider}_api",
        format_name="native",
        quote_currency=body.quote_currency,
        accounting_method=body.accounting_method,
        use_ptax=body.use_ptax,
    )


@router.post("/sync-wallet")
def sync_wallet_endpoint(
    body: SyncWalletIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    raw = _analyze_wallet_fetch(
        body.chain,
        body.address,
        body.etherscan_api_key,
        body.polygonscan_api_key,
    )
    if raw is None or raw.empty:
        raise HTTPException(status_code=400, detail="No on-chain transactions found for address.")

    result = analyze_from_dataframe(
        raw,
        format_name="native",
        accounting_method=body.accounting_method,
        country=body.country,
        quote_currency=body.quote_currency,
        use_ptax=body.use_ptax,
        max_amount_diff=0.01,
        max_time_diff_seconds=3600,
    )
    return _pipeline_response(
        db,
        current_user,
        result,
        filenames=f"onchain:{body.chain}:{body.address}",
        format_name=f"onchain:{body.chain}",
        quote_currency=body.quote_currency,
        accounting_method=body.accounting_method,
        use_ptax=body.use_ptax,
    )


@router.post("/br/wallet/onchain-analyze")
def wallet_onchain_analyze(
    body: BrWalletOnchainIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    raw = _analyze_wallet_fetch(
        body.chain,
        body.address,
        body.etherscan_api_key,
        body.polygonscan_api_key,
    )
    if raw is None or raw.empty:
        raise HTTPException(status_code=400, detail="No on-chain transactions found for address.")

    result = analyze_from_dataframe(
        raw,
        format_name="native",
        accounting_method=body.accounting_method,
        country=body.country,
        quote_currency=body.quote_currency,
        use_ptax=body.use_ptax,
        max_amount_diff=0.01,
        max_time_diff_seconds=3600,
    )
    return _pipeline_response(
        db,
        current_user,
        result,
        filenames=f"{body.chain}:{body.address}",
        format_name=f"onchain:{body.chain}",
        quote_currency=body.quote_currency,
        accounting_method=body.accounting_method,
        use_ptax=body.use_ptax,
    )
