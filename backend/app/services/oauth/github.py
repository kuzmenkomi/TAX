"""GitHub OAuth Provider — auth/login flow (NOT exchange OAuth)
Scopes: user:email (read-only, minimal)
"""
from __future__ import annotations

import httpx
from urllib.parse import urlencode
from typing import Dict, Any, Optional

from .base import BaseOAuthProvider, OAuthTokenResponse
from app.core.config import get_settings

_GITHUB_AUTH_URL  = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL  = "https://api.github.com/user"
_GITHUB_EMAIL_URL = "https://api.github.com/user/emails"


class GitHubProvider(BaseOAuthProvider):
    @property
    def provider_name(self) -> str:
        return "github"

    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        settings = get_settings()
        params = {
            "client_id":    settings.GITHUB_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope":        "user:email",
            "state":        state,
        }
        return f"{_GITHUB_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokenResponse:
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _GITHUB_TOKEN_URL,
                data={
                    "client_id":     settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code":          code,
                    "redirect_uri":  redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
        if "error" in data:
            raise ValueError(f"GitHub token error: {data.get('error_description', data['error'])}")
        return OAuthTokenResponse(
            access_token=data["access_token"],
            scope=data.get("scope"),
        )

    async def refresh_token(self, refresh_token: str) -> OAuthTokenResponse:
        # GitHub tokens do not expire by default (no refresh flow)
        raise NotImplementedError("GitHub tokens do not support refresh")

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }
        async with httpx.AsyncClient() as client:
            # 1. Primary profile
            user_resp = await client.get(_GITHUB_USER_URL, headers=headers)
            user_resp.raise_for_status()
            user_data: Dict[str, Any] = user_resp.json()

            # 2. If email is private, fetch from /user/emails
            if not user_data.get("email"):
                emails_resp = await client.get(_GITHUB_EMAIL_URL, headers=headers)
                if emails_resp.status_code == 200:
                    emails = emails_resp.json()
                    # Prefer verified primary
                    primary = next(
                        (e["email"] for e in emails if e.get("primary") and e.get("verified")),
                        next((e["email"] for e in emails if e.get("verified")), None),
                    )
                    user_data["email"] = primary

        return user_data
        # Returns: { id (int), login, email, name, avatar_url, ... }
