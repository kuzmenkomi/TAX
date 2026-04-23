import httpx
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from .base import BaseOAuthProvider, OAuthTokenResponse
from app.core.config import get_settings

class CoinbaseProvider(BaseOAuthProvider):
    @property
    def provider_name(self) -> str:
        return "coinbase"

    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        settings = get_settings()
        params = {
            "response_type": "code",
            "client_id": settings.COINBASE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "wallet:accounts:read,wallet:transactions:read",
            "account": "all"
        }
        return f"https://www.coinbase.com/oauth/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokenResponse:
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.coinbase.com/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.COINBASE_CLIENT_ID,
                    "client_secret": settings.COINBASE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                }
            )
            response.raise_for_status()
            data = response.json()
            return OAuthTokenResponse(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                expires_in=data.get("expires_in"),
                scope=data.get("scope")
            )

    async def refresh_token(self, refresh_token: str) -> OAuthTokenResponse:
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.coinbase.com/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.COINBASE_CLIENT_ID,
                    "client_secret": settings.COINBASE_CLIENT_SECRET,
                }
            )
            response.raise_for_status()
            data = response.json()
            return OAuthTokenResponse(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                expires_in=data.get("expires_in")
            )

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.coinbase.com/v2/user",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()["data"]
