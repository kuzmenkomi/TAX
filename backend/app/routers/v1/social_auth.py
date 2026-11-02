"""Social Auth Router — Google & GitHub login/register via OAuth.

Endpoints (NO authentication required — these ARE the login mechanism):
  GET /auth/google/login     → redirect to Google consent screen
  GET /auth/google/callback  → receive code, issue JWT, redirect to frontend
  GET /auth/github/login     → redirect to GitHub consent screen
  GET /auth/github/callback  → receive code, issue JWT, redirect to frontend

Deliberately separate from routers/v1/oauth.py which handles EXCHANGE OAuth
(Coinbase etc.) and REQUIRES an authenticated user.
"""
from __future__ import annotations

import logging
import secrets
from datetime import timedelta, timezone, datetime
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.cookies import set_auth_cookies
from app.core.db import get_db
from app.auth import create_access_token, create_refresh_token
from app.services import auth_service
from app.services.oauth.manager import oauth_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Social Auth"])

# --------------------------------------------------------------------------- #
#  Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _callback_url(settings, provider: str) -> str:
    """Backend callback URL passed to provider."""
    base = str(settings.FRONTEND_URL).rstrip("/")
    # We use the BACKEND URL (port 8000) for the actual code exchange
    backend = "http://localhost:8000"
    return f"{backend}/api/v1/auth/{provider}/callback"


def _issue_tokens_and_redirect(
    db: Session,
    response_obj,
    settings,
    user,
    frontend_redirect: str = "/dashboard",
) -> RedirectResponse:
    """Create JWT tokens, set cookies, redirect to frontend — or 2FA challenge."""
    if user.totp_enabled:
        tfa_token = create_access_token(
            {"sub": user.email, "tfa_pending": True},
            expires_delta=timedelta(minutes=5),
        )
        frontend_url = str(settings.FRONTEND_URL).rstrip("/")
        params = urlencode(
            {
                "requires_two_factor": "true",
                "two_factor_token": tfa_token,
            }
        )
        return RedirectResponse(url=f"{frontend_url}/oauth/callback?{params}", status_code=302)

    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    auth_service.save_refresh_token(
        db,
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    # Build frontend redirect URL with token as query param
    # (frontend reads it, saves to cookie, then removes from URL)
    frontend_url = str(settings.FRONTEND_URL).rstrip("/")
    params = urlencode({
        "access_token":  access_token,
        "refresh_token": refresh_token,
    })
    redirect_target = f"{frontend_url}/oauth/callback?{params}"

    redirect_response = RedirectResponse(url=redirect_target, status_code=302)
    # Also set httpOnly cookies so the frontend cookie flow works too
    set_auth_cookies(redirect_response, access_token, refresh_token, settings)
    return redirect_response


# --------------------------------------------------------------------------- #
#  Google                                                                      #
# --------------------------------------------------------------------------- #

@router.get("/auth/google/login", summary="Initiate Google OAuth login")
async def google_login():
    settings = get_settings()
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    state    = secrets.token_urlsafe(32)
    provider = oauth_manager.get_provider("google")
    auth_url = provider.get_auth_url(
        state=state,
        redirect_uri=_callback_url(settings, "google"),
    )
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/auth/google/callback", summary="Google OAuth callback")
async def google_callback(
    request: Request,
    code:  str   = Query(..., description="Authorization code from Google"),
    state: str   = Query(..., description="CSRF state token"),
    db:    Session = Depends(get_db),
):
    settings = get_settings()
    try:
        provider = oauth_manager.get_provider("google")
        tokens   = await provider.exchange_code(
            code,
            redirect_uri=_callback_url(settings, "google"),
        )
        info = await provider.get_user_info(tokens.access_token)

        provider_id = info.get("sub")
        email       = info.get("email")
        if not email or not provider_id:
            raise ValueError("Google did not return email or user ID")
        if not info.get("email_verified", True):
            raise ValueError("Google account email is not verified")

        user = auth_service.login_or_register_via_oauth(
            db,
            provider="google",
            provider_id=str(provider_id),
            email=email,
            name=info.get("name"),
            avatar_url=info.get("picture"),
            apply_geo=True,
            request=request,
        )
        logger.info("Audit log: Google OAuth login for %s (id=%s)", email, user.id)
        return _issue_tokens_and_redirect(db, None, settings, user)

    except Exception as exc:
        logger.error("Google OAuth callback error: %s", exc, exc_info=True)
        frontend_url = str(settings.FRONTEND_URL).rstrip("/")
        error_params = urlencode({"error": "google_oauth_failed"})
        return RedirectResponse(
            url=f"{frontend_url}/login?{error_params}",
            status_code=302,
        )


# --------------------------------------------------------------------------- #
#  GitHub                                                                      #
# --------------------------------------------------------------------------- #

@router.get("/auth/github/login", summary="Initiate GitHub OAuth login")
async def github_login():
    settings = get_settings()
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")

    state    = secrets.token_urlsafe(32)
    provider = oauth_manager.get_provider("github")
    auth_url = provider.get_auth_url(
        state=state,
        redirect_uri=_callback_url(settings, "github"),
    )
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/auth/github/callback", summary="GitHub OAuth callback")
async def github_callback(
    request: Request,
    code:  str   = Query(..., description="Authorization code from GitHub"),
    state: str   = Query("", description="CSRF state token"),
    db:    Session = Depends(get_db),
):
    settings = get_settings()
    try:
        provider = oauth_manager.get_provider("github")
        tokens   = await provider.exchange_code(
            code,
            redirect_uri=_callback_url(settings, "github"),
        )
        info = await provider.get_user_info(tokens.access_token)

        provider_id = info.get("id")
        email       = info.get("email")
        if not email:
            raise ValueError("Could not retrieve email from GitHub. Ensure 'user:email' scope is granted.")
        if not provider_id:
            raise ValueError("GitHub did not return a user ID")

        user = auth_service.login_or_register_via_oauth(
            db,
            provider="github",
            provider_id=str(provider_id),
            email=email,
            name=info.get("name") or info.get("login"),
            avatar_url=info.get("avatar_url"),
            apply_geo=True,
            request=request,
        )
        logger.info("Audit log: GitHub OAuth login for %s (id=%s)", email, user.id)
        return _issue_tokens_and_redirect(db, None, settings, user)

    except Exception as exc:
        logger.error("GitHub OAuth callback error: %s", exc, exc_info=True)
        frontend_url = str(settings.FRONTEND_URL).rstrip("/")
        error_params = urlencode({"error": "github_oauth_failed"})
        return RedirectResponse(
            url=f"{frontend_url}/login?{error_params}",
            status_code=302,
        )
