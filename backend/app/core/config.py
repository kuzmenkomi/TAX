"""Configuration - unified settings for the application."""
from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Literal

from cryptography.fernet import Fernet
from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_JWT_SECRETS = {
    "",
    "change-me-before-production",
    "dev-secret-key-change-in-production",
    "CHANGE_ME_IN_ENV_FOR_DEV_ONLY",
    "replace-with-a-random-secret",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_VERSION: str = "0.3.0"
    APP_NAME: str = "Declairo"

    # Database Configuration
    # Default: SQLite for dev, PostgreSQL for production
    DATABASE_URL: str = "sqlite:///./tax_app.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_ECHO: bool = False

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # Encryption - support for rotation via MultiFernet
    # The first key in the list is used for encryption. 
    # All keys are tried for decryption.
    ENCRYPTION_KEY: str = ""  # Legacy/Primary single key
    ENCRYPTION_KEYS: list[str] = [] # New: list of keys for rotation

    BREVO_API_KEY: str = ""
    BREVO_FROM_EMAIL: EmailStr = "noreply@example.com"

    # Coinbase OAuth (exchange connections)
    COINBASE_CLIENT_ID: str = ""
    COINBASE_CLIENT_SECRET: str = ""

    # Google OAuth (social login)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # GitHub OAuth (social login)
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # Blockchain explorer API keys (EVM chains)
    ETHERSCAN_API_KEY: str = ""
    BSCSCAN_API_KEY: str = ""
    POLYGONSCAN_API_KEY: str = ""

    # Error tracking
    SENTRY_DSN: str = ""

    # Stripe Billing
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # Stripe Price IDs (from Stripe Dashboard)
    STRIPE_PRICE_PRO: str = ""
    STRIPE_PRICE_BUSINESS: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    STRIPE_PRICE_ID_BUSINESS: str = ""

    FRONTEND_URL: str = "http://localhost:5173"
    FRONTEND_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    # Optional cookie Domain (e.g. ".example.com") for cross-subdomain auth cookies
    COOKIE_DOMAIN: str = ""

    # Redis for caching and background tasks (password required in production)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]
        if self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        return origins

    @property
    def all_encryption_keys(self) -> list[str]:
        """Combine old single key and new keys list, filtering empty values."""
        keys = []
        if self.ENCRYPTION_KEY:
            keys.append(self.ENCRYPTION_KEY)
        keys.extend(self.ENCRYPTION_KEYS)
        return [k for k in keys if k]

    @property
    def is_staging(self) -> bool:
        return self.APP_ENV == "staging"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_deployed_env(self) -> bool:
        return self.APP_ENV in {"staging", "production"}

    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL instead of SQLite."""
        return self.DATABASE_URL.startswith("postgresql")

    @property
    def stripe_price_pro(self) -> str:
        return (getattr(self, "STRIPE_PRICE_PRO", "") or getattr(self, "STRIPE_PRICE_ID_PRO", "")).strip()

    @property
    def stripe_price_business(self) -> str:
        return (
            getattr(self, "STRIPE_PRICE_BUSINESS", "")
            or getattr(self, "STRIPE_PRICE_ID_BUSINESS", "")
        ).strip()


@lru_cache()
def get_settings() -> Settings:
    """Cache settings so the app uses a single resolved configuration object."""
    settings = Settings()
    is_dev = settings.APP_ENV == "development"

    # Security check for production
    if not is_dev:
        if settings.JWT_SECRET_KEY in INSECURE_JWT_SECRETS:
            raise ValueError(
                "JWT_SECRET_KEY must be set to a strong, unique value outside development. "
                "Default or insecure keys are not allowed."
            )
        
        if not settings.all_encryption_keys:
            raise ValueError(
                "At least one valid encryption key must be set outside development "
                "via ENCRYPTION_KEY or ENCRYPTION_KEYS."
            )

        if settings.is_deployed_env and settings.DATABASE_URL.startswith("sqlite"):
            raise ValueError(
                "SQLite is not allowed outside development. "
                "Please configure a PostgreSQL connection via DATABASE_URL."
            )

        if settings.is_deployed_env and not (settings.REDIS_PASSWORD or "").strip():
            raise ValueError(
                "REDIS_PASSWORD must be set outside development for Redis-backed workers and caching."
            )

        if settings.STRIPE_SECRET_KEY and not (settings.STRIPE_WEBHOOK_SECRET or "").strip():
            raise ValueError(
                "STRIPE_WEBHOOK_SECRET must be set in production when STRIPE_SECRET_KEY is configured."
            )

        if settings.STRIPE_SECRET_KEY and not settings.stripe_price_pro:
            raise ValueError("STRIPE_PRICE_PRO (or STRIPE_PRICE_ID_PRO) must be set when Stripe billing is enabled.")

        if settings.STRIPE_SECRET_KEY and not settings.stripe_price_business:
            raise ValueError(
                "STRIPE_PRICE_BUSINESS (or STRIPE_PRICE_ID_BUSINESS) must be set when Stripe billing is enabled."
            )

    # Auto-generate keys for development if missing to ensure developer experience
    if is_dev:
        if settings.JWT_SECRET_KEY in INSECURE_JWT_SECRETS:
            settings.JWT_SECRET_KEY = secrets.token_urlsafe(64)
        if not settings.all_encryption_keys:
            settings.ENCRYPTION_KEY = Fernet.generate_key().decode()

    return settings
