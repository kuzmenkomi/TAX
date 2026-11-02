"""CSRF double-submit cookie validation for mutating API requests."""

from __future__ import annotations

import logging
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.cookies import CSRF_COOKIE, issue_csrf_token, set_csrf_cookie

logger = logging.getLogger(__name__)

# Paths that must not require CSRF (external webhooks, unauthenticated auth).
_CSRF_EXEMPT_PATHS: frozenset[str] = frozenset(
    {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/password-reset-request",
        "/api/v1/auth/password-reset",
        "/api/v1/auth/verify-email",
        "/api/v1/billing/webhook",
        # Legacy aliases (see app.api.versioning)
        "/v1/auth/login",
        "/v1/auth/register",
        "/v1/auth/refresh",
        "/v1/auth/password-reset-request",
        "/v1/auth/password-reset",
        "/v1/auth/verify-email",
        "/v1/billing/webhook",
    }
)


def _csrf_exempt(path: str) -> bool:
    return path in _CSRF_EXEMPT_PATHS


class CsrfMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        # Enforce CSRF only in production and staging (keeps CI/dev tests simple).
        if not settings.is_production and settings.APP_ENV != "staging":
            return await call_next(request)

        method = request.method.upper()
        path = request.url.path

        if method in ("GET", "HEAD", "OPTIONS"):
            response = await call_next(request)
            if CSRF_COOKIE not in request.cookies:
                set_csrf_cookie(response, issue_csrf_token(), settings)
            return response

        if _csrf_exempt(path):
            return await call_next(request)

        header = request.headers.get("X-CSRF-Token")
        cookie = request.cookies.get(CSRF_COOKIE)
        if not header or not cookie or header != cookie:
            logger.warning("CSRF validation failed for %s %s", method, path)
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed"},
            )

        return await call_next(request)
