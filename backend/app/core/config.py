"""Configuration - unified settings for the application."""
from __future__ import annotations

import os
import secrets
from functools import lru_cache
from typing import Literal

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

    # Coinbase OAuth
    COINBASE_CLIENT_ID: str = ""
    COINBASE_CLIENT_SECRET: str = ""

    # Blockchain explorer API keys (EVM chains)
    ETHERSCAN_API_KEY: str = ""
    BSCSCAN_API_KEY: str = ""
    POLYGONSCAN_API_KEY: str = ""

    # Error tracking
    SENTRY_DSN: str = ""

    FRONTEND_URL: str = "http://localhost:5173"
    FRONTEND_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

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
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL instead of SQLite."""
        return self.DATABASE_URL.startswith("postgresql")


@lru_cache()
def get_settings() -> Settings:
    """Cache settings so the app uses a single resolved configuration object."""
    settings = Settings()

    # Security check for production
    if settings.is_production:
        if settings.JWT_SECRET_KEY in INSECURE_JWT_SECRETS:
            raise ValueError(
                "JWT_SECRET_KEY must be set to a strong, unique value in production. "
                "Default or insecure keys are not allowed."
            )
        
        if not settings.all_encryption_keys:
            raise ValueError("At least one valid encryption key must be set in production via ENCRYPTION_KEYS.")

        if settings.DATABASE_URL.startswith("sqlite"):
            raise ValueError(
                "SQLite is not allowed in production. "
                "Please configure a PostgreSQL connection via DATABASE_URL."
            )

    # Auto-generate keys for development if missing to ensure developer experience
    if not settings.is_production:
        if settings.JWT_SECRET_KEY in INSECURE_JWT_SECRETS:
            settings.JWT_SECRET_KEY = secrets.token_urlsafe(64)
        if not settings.all_encryption_keys:
            # Fallback for dev if not provided
            settings.ENCRYPTION_KEY = "dev-insecure-but-present-key-for-local-runs-only"

    return settings
