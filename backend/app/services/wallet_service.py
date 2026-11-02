from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.accounting.price_fill import fill_missing_prices
from app.accounting.pricing import PriceService
from app.integrations.blockchain_explorer import fetch_wallet_transactions
from app.models import AnalysisRun, ImportJob, Transaction, User, WalletConnection
from app.services.portfolio_service import get_or_create_portfolio

BACKEND_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BACKEND_ROOT / "output"
SUPPORTED_CHAINS = {
    "ethereum",
    "polygon",
    "bsc",
    "bitcoin",
    "solana",
    "tron",
    "avalanche",
    "arbitrum",
    "optimism",
    "base",
}


def create_wallet(
    db: Session,
    user: User,
    chain: str,
    address: str,
    label: str | None = None,
) -> WalletConnection:
    normalized_chain = chain.strip().lower()
    normalized_address = address.strip()
    existing = (
        db.query(WalletConnection)
        .filter(
            WalletConnection.user_id == user.id,
            WalletConnection.chain == normalized_chain,
            WalletConnection.address == normalized_address,
        )
        .first()
    )
    if existing:
        return existing

    portfolio = get_or_create_portfolio(db, user)
    wallet = WalletConnection(
        user_id=user.id,
        portfolio_id=portfolio.id,
        chain=normalized_chain,
        address=normalized_address,
        label=(label or "").strip() or None,
        updated_at=datetime.now(timezone.utc),
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


def list_connections(db: Session, user: User) -> dict[str, list[dict[str, object]]]:
    from app.models import ExchangeConnection

    exchanges = (
        db.query(ExchangeConnection)
        .filter(ExchangeConnection.user_id == user.id)
        .all()
    )
    wallets = db.query(WalletConnection).filter(WalletConnection.user_id == user.id).all()

    # --- count transactions per wallet (from_wallet == str(wallet.id)) ---
    wallet_tx_counts: dict[int, int] = {}
    if wallets:
        rows = (
            db.query(Transaction.from_wallet, func.count(Transaction.id))
            .filter(
                Transaction.user_id == user.id,
                Transaction.from_wallet.in_([str(w.id) for w in wallets]),
            )
            .group_by(Transaction.from_wallet)
            .all()
        )
        wallet_tx_counts = {int(wid): cnt for wid, cnt in rows}

    from app.services.exchange_service import count_exchange_transactions

    return {
        "exchanges": [
            {
                "id": ex.id,
                "provider": ex.provider,
                "exchange_name": ex.exchange_name or ex.provider,
                "label": ex.label,
                "status": ex.status,
                "last_synced_at": ex.last_synced_at.isoformat() if ex.last_synced_at else None,
                "last_sync_at": ex.last_synced_at.isoformat() if ex.last_synced_at else None,
                "transaction_count": count_exchange_transactions(db, ex),
                "balance": 0.0,
            }
            for ex in exchanges
        ],
        "wallets": [
            {
                "id": wallet.id,
                "chain": wallet.chain,
                "address": wallet.address,
                "label": wallet.label,
                "transaction_count": wallet_tx_counts.get(wallet.id, 0),
                "last_synced_at": wallet.last_synced_at.isoformat() if wallet.last_synced_at else None,
                "sync_status": wallet.sync_status,
            }
            for wallet in wallets
        ],
    }


def import_blockchain_wallet(
    db: Session,
    user: User,
    chain: str,
    address: str,
    label: str | None = None,
) -> dict[str, object]:
    normalized_chain = chain.strip().lower()
    if normalized_chain not in SUPPORTED_CHAINS:
        supported = ", ".join(sorted(SUPPORTED_CHAINS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported chain: {normalized_chain}. Supported: {supported}",
        )

    wallet = create_wallet(db, user, normalized_chain, address, label)
    import_job = ImportJob(
        user_id=user.id,
        source=f"blockchain_{normalized_chain}",
        filename=f"{normalized_chain}_{address[:8]}",
        status="processing",
    )
    db.add(import_job)
    db.commit()
    db.refresh(import_job)

    try:
        df = fetch_wallet_transactions(wallet.address, normalized_chain)
        if df.empty:
            import_job.status = "done"
            import_job.finished_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "wallet_id": wallet.id,
                "import_job_id": import_job.id,
                "status": "done",
                "transactions_count": 0,
                "message": f"No transactions found for {wallet.address} on {normalized_chain}",
            }

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        df = fill_missing_prices(df, price_service=PriceService())
        csv_path = OUTPUT_DIR / f"blockchain_import_{import_job.id}.csv"
        df.to_csv(csv_path, index=False)

        analysis_run = AnalysisRun(
            user_id=user.id,
            csv_rel_path=str(csv_path.relative_to(BACKEND_ROOT)).replace("\\", "/"),
            summary_json=json.dumps(
                {
                    "blockchain": {
                        "chain": normalized_chain,
                        "address": wallet.address,
                        "transaction_count": len(df),
                        "assets": df["asset"].unique().tolist(),
                    }
                }
            ),
        )
        db.add(analysis_run)
        import_job.status = "done"
        import_job.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(analysis_run)

        from app.services.transaction_service import save_transactions_from_df
        save_transactions_from_df(db, user.id, analysis_run.id, df)

        return {
            "wallet_id": wallet.id,
            "import_job_id": import_job.id,
            "analysis_run_id": analysis_run.id,
            "status": "done",
            "transactions_count": len(df),
            "assets": df["asset"].unique().tolist(),
        }
    except Exception as exc:
        import_job.status = "failed"
        import_job.error = str(exc)
        import_job.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import blockchain wallet: {exc}",
        ) from exc


def delete_wallet(
    db: Session,
    user: User,
    wallet_id: int,
) -> WalletConnection:
    wallet = (
        db.query(WalletConnection)
        .filter(
            WalletConnection.id == wallet_id,
            WalletConnection.user_id == user.id,
        )
        .first()
    )
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    db.delete(wallet)
    db.commit()
    return wallet
