"""Google OAuth Provider — auth/login flow (NOT exchange OAuth)
Scopes: openid email profile
"""
from __future__ import annotations

import httpx
from urllib.parse import urlencode
from typing import Dict, Any

from .base import BaseOAuthProvider, OAuthTokenResponse
from app.core.config import get_settings

_GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO  = "https://openidconnect.googleapis.com/v1/userinfo"


class GoogleProvider(BaseOAuthProvider):
    @property
    def provider_name(self) -> str:
        return "google"

    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        settings = get_settings()
        params = {
            "response_type": "code",
            "client_id":     settings.GOOGLE_CLIENT_ID,
            "redirect_uri":  redirect_uri,
            "scope":         "openid email profile",
            "state":         state,
            "access_type":   "offline",
            "prompt":        "select_account",
        }
        return f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokenResponse:
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "grant_type":    "authorization_code",
                    "code":          code,
                    "client_id":     settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri":  redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
        return OAuthTokenResponse(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in"),
            scope=data.get("scope"),
        )

    async def refresh_token(self, refresh_token: str) -> OAuthTokenResponse:
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "grant_type":    "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id":     settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        return OAuthTokenResponse(
            access_token=data["access_token"],
            expires_in=data.get("expires_in"),
        )

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                _GOOGLE_USERINFO,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            return resp.json()
        # Returns: { sub, email, email_verified, name, picture, ... }
