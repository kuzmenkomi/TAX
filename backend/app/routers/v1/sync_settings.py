from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth import get_current_user
from app.core.db import get_db
from app.models import User, WalletConnection, ExchangeConnection

router = APIRouter(prefix="/sync-settings", tags=["sync"])

class AutoSyncToggleRequest(BaseModel):
    enabled: bool

class SyncIntervalRequest(BaseModel):
    interval_hours: int

@router.patch("/wallet/{wallet_id}/auto-sync")
def toggle_wallet_auto_sync(
    wallet_id: int,
    body: AutoSyncToggleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet = db.query(WalletConnection).filter(
        WalletConnection.id == wallet_id,
        WalletConnection.user_id == current_user.id
    ).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    wallet.auto_sync_enabled = body.enabled
    db.commit()
    return {"status": "success", "wallet_id": wallet_id, "auto_sync_enabled": body.enabled}

@router.patch("/exchange/{exchange_id}/auto-sync")
def toggle_exchange_auto_sync(
    exchange_id: int,
    body: AutoSyncToggleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exchange = db.query(ExchangeConnection).filter(
        ExchangeConnection.id == exchange_id,
        ExchangeConnection.user_id == current_user.id
    ).first()
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    exchange.auto_sync_enabled = body.enabled
    db.commit()
    return {"status": "success", "exchange_id": exchange_id, "auto_sync_enabled": body.enabled}

@router.get("/status")
def get_detailed_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns detailed sync metadata for all connections to show in UI."""
    wallets = db.query(WalletConnection).filter(WalletConnection.user_id == current_user.id).all()
    exchanges = db.query(ExchangeConnection).filter(ExchangeConnection.user_id == current_user.id).all()
    
    return {
        "wallets": [
            {
                "id": w.id,
                "chain": w.chain,
                "address": w.address,
                "sync_status": w.sync_status,
                "auto_sync_enabled": w.auto_sync_enabled,
                "last_synced_at": w.last_synced_at.isoformat() if w.last_synced_at else None,
                "next_sync_at": w.next_sync_at.isoformat() if w.next_sync_at else None,
                "last_error": w.last_error,
                "last_block": w.last_block_synced
            }
            for w in wallets
        ],
        "exchanges": [
            {
                "id": e.id,
                "exchange_name": e.exchange_name or e.provider,
                "sync_status": e.sync_status,
                "auto_sync_enabled": e.auto_sync_enabled,
                "last_synced_at": e.last_synced_at.isoformat() if e.last_synced_at else None,
                "next_sync_at": e.next_sync_at.isoformat() if e.next_sync_at else None,
                "last_error": e.last_error
            }
            for e in exchanges
        ]
    }
