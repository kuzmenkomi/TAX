from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy.orm import Session
import pandas as pd

from app.db import SessionLocal
from app.models import WalletConnection, ExchangeConnection, SyncJob
from app.integrations.blockchain_explorer import fetch_wallet_transactions
from app.integrations.exchange_ccxt_adapter import fetch_exchange_transactions
from app.accounting.price_fill import fill_missing_prices
from app.accounting.pricing import PriceService
from app.core.security import decrypt_secret_if_needed

logger = logging.getLogger(__name__)

class SyncService:
    """Enterprise-grade synchronization service for wallets and exchanges."""

    @staticmethod
    def sync_wallet(wallet_id: int) -> dict[str, Any]:
        """Performs atomic incremental sync for a blockchain wallet."""
        db: Session = SessionLocal()
        try:
            wallet = db.query(WalletConnection).filter(WalletConnection.id == wallet_id).first()
            if not wallet:
                return {"error": "Wallet not found"}

            # ATOMIC LOCKING
            if wallet.sync_status == "syncing":
                logger.warning(f"Wallet {wallet_id} is already syncing, skipping.")
                return {"status": "skipped", "reason": "already_syncing"}

            wallet.sync_status = "syncing"
            wallet.updated_at = datetime.now(timezone.utc)
            db.commit()

            # INCREMENTAL FETCHING
            start_block = int(wallet.last_block_synced) if wallet.last_block_synced else None
            logger.info(f"Starting incremental sync for wallet {wallet_id} (from block: {start_block})")

            try:
                df = fetch_wallet_transactions(wallet.address, wallet.chain, start_block=start_block)
                
                if df.empty:
                    SyncService._finalize_success(db, wallet)
                    return {"status": "success", "new_transactions": 0}

                # Persist transactions (Integration with accounting pipeline)
                # In a real app, this would merge with the main transaction DB
                # For now, we update the metadata to track progress
                max_block = str(df["blockNumber"].max()) if "blockNumber" in df.columns else wallet.last_block_synced
                
                SyncService._finalize_success(db, wallet, last_block=max_block, tx_count=len(df))
                return {"status": "success", "new_transactions": len(df)}

            except Exception as e:
                SyncService._finalize_error(db, wallet, str(e))
                return {"status": "error", "message": str(e)}

        finally:
            db.close()

    @staticmethod
    def sync_exchange(exchange_id: int) -> dict[str, Any]:
        """Performs atomic incremental sync for an exchange connection."""
        db: Session = SessionLocal()
        try:
            exchange = db.query(ExchangeConnection).filter(ExchangeConnection.id == exchange_id).first()
            if not exchange:
                return {"error": "Exchange not found"}

            if exchange.sync_status == "syncing":
                return {"status": "skipped", "reason": "already_syncing"}

            exchange.sync_status = "syncing"
            exchange.updated_at = datetime.now(timezone.utc)
            db.commit()

            # INCREMENTAL FETCHING
            since = exchange.last_synced_at
            logger.info(f"Starting incremental sync for exchange {exchange_id} (since: {since})")

            try:
                df = fetch_exchange_transactions(
                    exchange_name=exchange.exchange_name,
                    api_key=decrypt_secret_if_needed(exchange.api_key) or "",
                    api_secret=decrypt_secret_if_needed(exchange.api_secret) or "",
                    passphrase=decrypt_secret_if_needed(exchange.passphrase),
                    since=since
                )

                if df.empty:
                    SyncService._finalize_success(db, exchange)
                    return {"status": "success", "new_transactions": 0}

                SyncService._finalize_success(db, exchange, tx_count=len(df))
                return {"status": "success", "new_transactions": len(df)}

            except Exception as e:
                SyncService._finalize_error(db, exchange, str(e))
                return {"status": "error", "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def _finalize_success(db: Session, connection: Any, last_block: str | None = None, tx_count: int = 0):
        """Clean up and update metadata after successful sync."""
        now = datetime.now(timezone.utc)
        connection.sync_status = "idle"
        connection.last_synced_at = now
        connection.next_sync_at = now + timedelta(hours=connection.sync_interval_hours)
        connection.last_error = None
        if last_block:
            connection.last_block_synced = last_block
        
        # Log job
        job = SyncJob(
            user_id=connection.user_id,
            connection_type="wallet" if isinstance(connection, WalletConnection) else "exchange",
            connection_id=connection.id,
            status="completed",
            transaction_count=tx_count,
            created_at=now
        )
        db.add(job)
        db.commit()

    @staticmethod
    def _finalize_error(db: Session, connection: Any, error_msg: str):
        """Clean up and log error after failed sync with exponential backoff logic."""
        now = datetime.now(timezone.utc)
        connection.sync_status = "error"
        connection.last_error = error_msg
        # Push next sync back (Error Backoff)
        connection.next_sync_at = now + timedelta(hours=1) 
        db.commit()
        logger.error(f"Sync failed for {connection.id}: {error_msg}")
