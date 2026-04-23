from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.db import get_db
from app.models import User, WalletConnection
from app.schemas.wallet import BlockchainImportRequest, WalletConnectRequest, WalletResponse
from app.services import wallet_service

router = APIRouter(tags=["wallet"])


@router.post("/br/wallet", response_model=WalletResponse)
def connect_wallet(
    body: WalletConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WalletResponse:
    wallet = wallet_service.create_wallet(db, current_user, body.chain, body.address, body.label)
    return WalletResponse.model_validate(wallet)


@router.post("/br/wallet/import-blockchain")
def import_blockchain_wallet(
    body: BlockchainImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
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
