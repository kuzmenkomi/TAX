"""Shared observability bootstrap for API and worker processes."""

from __future__ import annotations

import os

import sentry_sdk

from app.core.config import Settings
from app.core.logging_config import setup_logging


def _scrub_sentry_event(event: dict, hint: dict) -> dict | None:  # noqa: ARG001
    """Remove common sensitive headers from captured Sentry events."""
    if "request" in event and isinstance(event["request"], dict):
        headers = event["request"].get("headers")
        if isinstance(headers, dict):
            for key in ("Authorization", "Cookie", "Set-Cookie"):
                if key in headers:
                    headers[key] = "[redacted]"
    return event


def setup_observability(settings: Settings) -> None:
    """Configure logging first, then optional Sentry."""
    setup_logging(json_format=settings.is_deployed_env)

    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.APP_ENV,
            release=settings.APP_VERSION,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0")),
            send_default_pii=False,
            before_send=_scrub_sentry_event,
        )
