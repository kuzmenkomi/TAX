from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class OAuthTokenResponse:
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = "Bearer"
    scope: Optional[str] = None

class BaseOAuthProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Generate the authorization URL for the user."""
        pass

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> OAuthTokenResponse:
        """Exchange the authorization code for tokens."""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> OAuthTokenResponse:
        """Refresh an expired access token."""
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Fetch basic user info from the provider to verify connection."""
        pass
