import secrets
import time
from typing import Dict, Any, Optional
import jwt
from jwt import PyJWTError as JWTError
from fastapi import HTTPException
from app.core.config import get_settings
from .base import BaseOAuthProvider
from .coinbase import CoinbaseProvider
from .google import GoogleProvider
from .github import GitHubProvider

class OAuthManager:
    def __init__(self):
        self._providers: Dict[str, BaseOAuthProvider] = {
            "coinbase": CoinbaseProvider(),
            "google":   GoogleProvider(),
            "github":   GitHubProvider(),
        }

    def get_provider(self, name: str) -> BaseOAuthProvider:
        provider = self._providers.get(name.lower())
        if not provider:
            raise HTTPException(status_code=400, detail=f"OAuth provider '{name}' not supported")
        return provider

    def generate_state(self, user_id: int) -> str:
        """Generate a signed state token for CSRF protection."""
        settings = get_settings()
        payload = {
            "user_id": user_id,
            "exp": int(time.time()) + 600,  # 10 minutes
            "nonce": secrets.token_urlsafe(16),
        }
        
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    def verify_state(self, state: str, expected_user_id: int) -> bool:
        """Verify the state token."""
        settings = get_settings()
        try:
            payload = jwt.decode(state, settings.JWT_SECRET_KEY, algorithms=["HS256"])
            if payload.get("user_id") != expected_user_id:
                return False
            return True
        except (JWTError, KeyError):
            return False

# Global instance
oauth_manager = OAuthManager()
