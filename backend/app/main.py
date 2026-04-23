"""Main FastAPI application - unified backend with improved architecture"""
from __future__ import annotations

import os
from pathlib import Path

from app.api.server import create_app

BACKEND_ROOT = Path(__file__).resolve().parents[1]
app = create_app()

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=not os.getenv("PRODUCTION"),
    )
