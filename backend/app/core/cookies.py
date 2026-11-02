"""HTTP cookie helpers for httpOnly auth tokens and CSRF double-submit."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from fastapi import Response

if TYPE_CHECKING:
    from app.core.config import Settings

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"


def _cookie_common(settings: "Settings") -> dict:
    secure = settings.is_deployed_env
    domain = (getattr(settings, "COOKIE_DOMAIN", None) or "").strip() or None
    out: dict = {
        "secure": secure,
        "samesite": "lax",
        "path": "/",
    }
    if domain:
        out["domain"] = domain
    return out


def issue_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: str, settings: "Settings") -> None:
    response.set_cookie(
        key=CSRF_COOKIE,
        value=token,
        httponly=False,
        max_age=60 * 60 * 24 * 365,
        **_cookie_common(settings),
    )


def set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
    settings: "Settings",
    csrf_token: str | None = None,
) -> None:
    """Set httpOnly access/refresh cookies and readable CSRF cookie."""
    common = _cookie_common(settings)
    # Use the same lifetime as the JWT token itself
    access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        httponly=True,
        max_age=access_max_age,
        **common,
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        **common,
    )
    set_csrf_cookie(response, csrf_token or issue_csrf_token(), settings)


def set_impersonation_access_cookie(
    response: Response,
    *,
    access_token: str,
    settings: "Settings",
    max_age_seconds: int = 30 * 60,
) -> None:
    """Short-lived access cookie for support impersonation; clears refresh to avoid token confusion."""
    common = _cookie_common(settings)
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        httponly=True,
        max_age=max_age_seconds,
        **common,
    )
    response.delete_cookie(key=REFRESH_COOKIE, path="/", domain=common.get("domain"))


def clear_auth_cookies(response: Response, settings: "Settings") -> None:
    common = _cookie_common(settings)
    for key in (ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(key=key, path="/", domain=common.get("domain"))
