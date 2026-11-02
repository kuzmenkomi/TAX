from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
import logging

from app.auth import (
    _revoked_tokens,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_access_token,
    get_current_user,
    get_user_by_email,
    require_not_impersonating,
    verify_tfa_pending_token,
)
from app.core.config import get_settings
from app.core.cookies import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from app.core.db import get_db
from app.core.limiter import limiter
from app.email_service import get_email_service
from app.models import User
from app.schemas.auth import (
    EmailVerifyRequest,
    LoginRequest,
    LoginTwoFactorCompleteRequest,
    MeResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    SupportAccessResponse,
    SupportAccessUpdateRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserInfo,
)
from app.services import auth_service
from app.services import support_impersonation_service
from app.services import two_factor_service
from app.services.jurisdiction_geo_service import (
    _jurisdiction_display_name,
    apply_registration_geo,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"], prefix="")


@router.post("/auth/logout")
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    token = get_access_token(request)
    if token:
        _revoked_tokens.add(token)
    clear_auth_cookies(response, get_settings())
    return {"status": "logged_out"}


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
    response: Response,
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user, verification_token = auth_service.register_user(db, body.email, body.password)
    apply_registration_geo(db, user, request)
    try:
        get_email_service().send_verification_email(user.email, verification_token)
    except Exception:
        pass  # Email failures should not block registration

    logger.info("Audit log: New user registered with email %s", user.email)

    created_at = user.created_at.replace(tzinfo=timezone.utc).isoformat() if user.created_at else ""
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    auth_service.save_refresh_token(
        db,
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    set_auth_cookies(
        response,
        access_token=access_token,
        refresh_token=refresh_token,
        settings=get_settings(),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(id=user.id, email=user.email, created_at=created_at),
    )


@router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("100/minute")
def login_user(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = authenticate_user(
        db,
        email=body.email.strip().lower(),
        password=body.password,
    )
    if not user:
        logger.warning("Audit log: Failed login attempt for email %s", body.email.strip().lower())
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")

    logger.info("Audit log: Password verified for user %s", user.email)

    if user.totp_enabled:
        tfa_token = create_access_token(
            {"sub": user.email, "tfa_pending": True},
            expires_delta=timedelta(minutes=5),
        )
        return TokenResponse(
            requires_two_factor=True,
            two_factor_token=tfa_token,
            access_token=None,
            refresh_token=None,
            user=None,
        )

    created_at = user.created_at.replace(tzinfo=timezone.utc).isoformat() if user.created_at else ""
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    auth_service.save_refresh_token(
        db,
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    set_auth_cookies(
        response,
        access_token=access_token,
        refresh_token=refresh_token,
        settings=get_settings(),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(id=user.id, email=user.email, created_at=created_at),
    )


@router.post("/auth/login/2fa", response_model=TokenResponse)
@limiter.limit("30/minute")
def login_two_factor(
    request: Request,
    response: Response,
    body: LoginTwoFactorCompleteRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    email = verify_tfa_pending_token(body.two_factor_token)
    user = get_user_by_email(db, email)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    if not user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is not enabled for this account")
    if not two_factor_service.verify_user_totp_code(user, body.code):
        logger.warning("Audit log: Invalid 2FA code for user %s", email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authenticator code")

    logger.info("Audit log: Successful login (2FA) for user %s", user.email)

    created_at = user.created_at.replace(tzinfo=timezone.utc).isoformat() if user.created_at else ""
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    auth_service.save_refresh_token(
        db,
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    set_auth_cookies(
        response,
        access_token=access_token,
        refresh_token=refresh_token,
        settings=get_settings(),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(id=user.id, email=user.email, created_at=created_at),
    )


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    body: TokenRefreshRequest | None = Body(default=None),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access token and refresh token."""
    rt = (body.refresh_token if body else None) or request.cookies.get(REFRESH_COOKIE)
    if not rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    user = auth_service.verify_refresh_token(db, rt)

    access_token = create_access_token({"sub": user.email})
    new_refresh_token = create_refresh_token({"sub": user.email})

    auth_service.save_refresh_token(
        db,
        user_id=user.id,
        token=new_refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoke_others=False,
    )

    set_auth_cookies(
        response,
        access_token=access_token,
        refresh_token=new_refresh_token,
        settings=get_settings(),
    )

    created_at = user.created_at.replace(tzinfo=timezone.utc).isoformat() if user.created_at else ""
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=UserInfo(id=user.id, email=user.email, created_at=created_at),
    )


@router.get("/auth/me", response_model=MeResponse)
def read_me(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> MeResponse:
    imp = getattr(request.state, "impersonation", None)
    exp_iso, active = support_impersonation_service.support_access_public_fields(current_user)
    jcode = (getattr(current_user, "jurisdiction_code", None) or "BR").upper()
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        is_email_verified=current_user.is_email_verified,
        role=str(current_user.role or "user"),
        two_factor_enabled=bool(current_user.totp_enabled),
        jurisdiction_code=jcode,
        jurisdiction_name=_jurisdiction_display_name(jcode),
        impersonation=dict(imp) if imp else None,
        allow_support_until=exp_iso,
        support_access_active=active,
    )


@router.patch("/auth/me/support-access", response_model=SupportAccessResponse)
@limiter.limit("60/hour")
def update_support_access(
    request: Request,
    body: SupportAccessUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_not_impersonating),
) -> SupportAccessResponse:
    """Customer enables or revokes the 24h window for support impersonation (Settings toggle)."""
    if body.allow:
        current_user.allow_support_until = datetime.now(timezone.utc) + support_impersonation_service.SUPPORT_ACCESS_DURATION
    else:
        current_user.allow_support_until = None
    db.commit()
    db.refresh(current_user)
    exp_iso, active = support_impersonation_service.support_access_public_fields(current_user)
    logger.info(
        "support_access_updated user_id=%s allow=%s until=%s",
        current_user.id,
        body.allow,
        exp_iso,
    )
    return SupportAccessResponse(allow_support_until=exp_iso, support_access_active=active)


@router.delete("/auth/me")
def delete_me(
    request: Request,
    response: Response,
    current_user: User = Depends(require_not_impersonating),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete all user data and the account itself (LGPD/GDPR compliance)."""
    auth_service.delete_user_data(db, current_user.id)
    token = get_access_token(request)
    if token:
        _revoked_tokens.add(token)
    clear_auth_cookies(response, get_settings())
    logger.info("Audit log: User %s (id=%s) deleted their account.", current_user.email, current_user.id)
    return {"status": "ok", "message": "Account and all associated data deleted successfully"}


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
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/auth/export-summary")
def export_data_summary(current_user: User = Depends(get_current_user)) -> dict[str, object]:
    """
    Lightweight DSAR-style summary (extend with ZIP/CSV export of full user data).
    """
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "is_email_verified": current_user.is_email_verified,
        "message": "Request full data export via support; this endpoint returns a minimal summary only.",
    }
