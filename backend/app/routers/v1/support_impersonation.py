"""Support staff impersonation API — audited access to view a customer account as that user."""
from __future__ import annotations

import logging
from datetime import timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.auth import (
    _revoked_tokens,
    create_access_token,
    get_access_token,
    get_current_user,
)
from app.core.config import get_settings
from app.core.cookies import clear_auth_cookies, set_impersonation_access_cookie
from app.core.db import get_db
from app.models import User
from app.schemas.auth import SupportImpersonationStartRequest
from app.services import support_impersonation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/support/staff", tags=["Support Staff"])


def require_staff_not_impersonating(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if getattr(request.state, "impersonation", None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="End the current impersonation session before starting another.",
        )
    support_impersonation_service.assert_staff(current_user)
    return current_user


@router.post("/impersonation/start")
def impersonation_start(
    request: Request,
    response: Response,
    body: SupportImpersonationStartRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_staff_not_impersonating),
):
    subject = support_impersonation_service.lookup_subject_user(
        db,
        user_id=body.user_id,
        email=str(body.email) if body.email else None,
    )
    log = support_impersonation_service.start_impersonation(
        db,
        actor=actor,
        subject=subject,
        reason=body.reason,
        request=request,
    )
    access = create_access_token(
        {
            "sub": subject.email,
            "imp": True,
            "act": actor.email,
            "sid": log.id,
        },
        expires_delta=timedelta(minutes=30),
    )
    settings = get_settings()
    set_impersonation_access_cookie(response, access_token=access, settings=settings, max_age_seconds=30 * 60)
    return {
        "access_token": access,
        "expires_in": 30 * 60,
        "token_type": "bearer",
        "subject": {"id": subject.id, "email": subject.email},
    }


@router.post("/impersonation/end")
def impersonation_end(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    imp = getattr(request.state, "impersonation", None)
    if not imp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not in an impersonation session")

    log_id = int(imp["log_id"])
    log = support_impersonation_service.active_log_for_token(db, log_id)
    if not log:
        clear_auth_cookies(response, get_settings())
        return {"status": "ended"}

    support_impersonation_service.end_impersonation(db, log)
    token = get_access_token(request)
    if token:
        _revoked_tokens.add(token)
    clear_auth_cookies(response, get_settings())
    logger.info("impersonation ended by subject session log_id=%s", log_id)
    return {"status": "ended", "message": "Session closed. Sign in again as support if needed."}


@router.get("/impersonation/status")
def impersonation_status(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    imp = getattr(request.state, "impersonation", None)
    if not imp:
        return {"active": False}
    return {
        "active": True,
        "actor_email": imp.get("actor_email"),
        "subject_email": imp.get("subject_email"),
        "log_id": imp.get("log_id"),
    }
