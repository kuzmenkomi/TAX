from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.versioning import register_v1_aliases
from app.core.config import get_settings
from app.core.db import Base, engine, initialize_database
from app.core.limiter import limiter
from app.routers import api_router
import app.models  # Register all models with SQLAlchemy before metadata.create_all()

BACKEND_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = BACKEND_ROOT / "data" / "runs"

logger = logging.getLogger(__name__)


def _init_sentry(settings) -> None:
    """Initialize Sentry error tracking if DSN is configured."""
    dsn = settings.SENTRY_DSN
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=settings.APP_ENV,
            release=f"declairo@{settings.APP_VERSION}",
            traces_sample_rate=0.2 if settings.is_production else 1.0,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            send_default_pii=False,
        )
        logger.info("✅ Sentry initialized (env=%s)", settings.APP_ENV)
    except ImportError:
        logger.warning("sentry-sdk not installed — error tracking disabled")
    except Exception as e:
        logger.error("Sentry init failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()

    # Sentry
    _init_sentry(settings)

    # Database
    if not settings.is_production:
        Base.metadata.create_all(bind=engine)
        initialize_database()

    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    # Background scheduler
    from app.scheduler import start_scheduler, stop_scheduler
    start_scheduler()

    yield

    # Shutdown
    stop_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Declairo API",
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    @app.get("/health", tags=["system"])
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error. Please contact support."},
        )

    @app.middleware("http")
    async def request_logging(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
        return response

    if settings.is_production:
        app.add_middleware(HTTPSRedirectMiddleware)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    # Production CORS Hardening
    origins = settings.cors_origins
    if settings.is_production and not origins:
        logger.error("❌ CRITICAL: No CORS origins defined in production!")
        # Fallback to empty to deny everything if misconfigured
        origins = []

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
        expose_headers=["Content-Disposition"],
    )

    app.include_router(api_router, prefix="/api")
    register_v1_aliases(app)
    return app


app = create_app()

__all__ = ["app", "BACKEND_ROOT", "RUNS_DIR", "create_app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=not os.getenv("PRODUCTION"),
    )
