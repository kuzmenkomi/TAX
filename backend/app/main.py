"""Main FastAPI application - unified backend with improved architecture."""

from __future__ import annotations

import os
from pathlib import Path

from app.core.config import get_settings
from app.core.observability import setup_observability

settings = get_settings()
setup_observability(settings)

from app.api.server import create_app  # noqa: E402

BACKEND_ROOT = Path(__file__).resolve().parents[1]
app = create_app()

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("UVICORN_HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("APP_ENV", "development") == "development",
    )
