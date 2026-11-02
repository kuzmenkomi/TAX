"""Two-factor authentication (TOTP) HTTP API — thin wrapper over two_factor_service."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_not_impersonating
from app.core.config import get_settings
from app.core.db import get_db
from app.models import User
from app.schemas.auth import (
    TwoFactorConfirmRequest,
    TwoFactorDisableRequest,
    TwoFactorSetupBeginResponse,
)
from app.services import two_factor_service

router = APIRouter(prefix="/auth/2fa", tags=["Two-Factor Auth"])


@router.get("/status")
def two_factor_status(
    current_user: User = Depends(get_current_user),
) -> dict:
    return {
        "enabled": bool(current_user.totp_enabled),
        "pending_setup": bool(current_user.totp_pending) and not current_user.totp_enabled,
    }


@router.post("/setup/begin", response_model=TwoFactorSetupBeginResponse)
def two_factor_setup_begin(
    current_user: User = Depends(require_not_impersonating),
    db: Session = Depends(get_db),
) -> TwoFactorSetupBeginResponse:
    settings = get_settings()
    issuer = settings.APP_NAME or "Declairo"
    _secret, uri = two_factor_service.begin_totp_setup(db, current_user, issuer=issuer)
    return TwoFactorSetupBeginResponse(otpauth_uri=uri, issuer=issuer)


@router.post("/setup/confirm", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def two_factor_setup_confirm(
    body: TwoFactorConfirmRequest,
    current_user: User = Depends(require_not_impersonating),
    db: Session = Depends(get_db),
) -> Response:
    two_factor_service.confirm_totp_setup(db, current_user, body.code)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/setup/cancel", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def two_factor_setup_cancel(
    current_user: User = Depends(require_not_impersonating),
    db: Session = Depends(get_db),
) -> Response:
    two_factor_service.cancel_totp_setup(db, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/disable", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def two_factor_disable(
    body: TwoFactorDisableRequest,
    current_user: User = Depends(require_not_impersonating),
    db: Session = Depends(get_db),
) -> Response:
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth-only accounts cannot disable 2FA with password. Contact support.",
        )
    two_factor_service.disable_totp(db, current_user, body.password, body.code)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
