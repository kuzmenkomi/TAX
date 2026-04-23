from __future__ import annotations

from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
import logging

from app.auth import authenticate_user, create_access_token, get_current_user
from app.core.db import get_db
from app.core.limiter import limiter
from app.email_service import get_email_service
from app.models import User
from app.schemas.auth import (
    EmailVerifyRequest,
    LoginRequest,
    MeResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
    UserInfo,
)
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"], prefix="")


@router.post(
    "/auth/register",
    response_model=TokenResponse,
    summary="User Registration",
    description="Register a new user account with email and password",
    responses={
        200: {"description": "Successfully registered and returned access token"},
        422: {"description": "Invalid request parameters"},
        429: {"description": "Too many registration attempts"},
    },
)
@limiter.limit("100/hour")
def register_user(
    request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user, verification_token = auth_service.register_user(db, body.email, body.password)
    try:
        get_email_service().send_verification_email(user.email, verification_token)
    except Exception:
        pass  # Email failures should not block registration
    
    logger.info(f"Audit log: New user registered with email {user.email}")
    
    created_at = user.created_at.replace(tzinfo=timezone.utc).isoformat() if user.created_at else ""
    return TokenResponse(
        access_token=create_access_token({"sub": user.email}),
        user=UserInfo(id=user.id, email=user.email, created_at=created_at),
    )


@router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("100/minute")
def login_user(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = authenticate_user(
        db,
        email=body.email.strip().lower(),
        password=body.password,
    )
    if not user:
        logger.warning(f"Audit log: Failed login attempt for email {body.email.strip().lower()}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    
    logger.info(f"Audit log: Successful login for user {user.email}")
    
    created_at = user.created_at.replace(tzinfo=timezone.utc).isoformat() if user.created_at else ""
    return TokenResponse(
        access_token=create_access_token({"sub": user.email}),
        user=UserInfo(id=user.id, email=user.email, created_at=created_at),
    )


@router.get("/auth/me", response_model=MeResponse)
def read_me(current_user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        is_email_verified=current_user.is_email_verified,
    )


@router.post("/auth/verify-email")
@limiter.limit("100/hour")
def verify_email(
    request: Request,
    body: EmailVerifyRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    auth_service.verify_email(db, body.token)
    return {"status": "ok", "message": "Email verified successfully"}


@router.post("/auth/password-reset-request")
@limiter.limit("100/hour")
def request_password_reset(
    request: Request,
    body: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    token = auth_service.request_password_reset(db, body.email)
    if token:
        get_email_service().send_password_reset_email(body.email, token)
    return {"status": "ok", "message": "If user exists, reset email sent"}


@router.post("/auth/password-reset")
@limiter.limit("100/hour")
def reset_password(
    request: Request,
    body: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    auth_service.confirm_password_reset(db, body.token, body.new_password)
    logger.info("Audit log: Successful password reset via token")
    return {"status": "ok", "message": "Password reset successfully"}


@router.get("/auth/health")
def auth_health() -> dict[str, str]:
    from datetime import datetime, timezone
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
