from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import app.models
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.csrf import CsrfMiddleware
from app.api.versioning import register_v1_aliases
from app.core.config import Settings, get_settings
from app.core.db import Base, engine, get_db, initialize_database
from app.core.limiter import limiter
from app.core.migration_check import verify_alembic_at_head
from app.core.observability import setup_observability
from app.routers import api_router

BACKEND_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = BACKEND_ROOT / "data" / "runs"

logger = logging.getLogger(__name__)


async def _health_payload(db: Session, settings: Settings) -> dict[str, object]:
    health: dict[str, object] = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "checks": {
            "database": {"status": "up"},
            "redis": {"status": "unknown"},
        },
        "observability": {
            "log_format": "json" if settings.is_deployed_env else "plain",
            "sentry": "enabled" if settings.SENTRY_DSN else "disabled",
        },
    }

    db_started = time.perf_counter()
    try:
        db.execute(select(1))
        health["checks"]["database"]["latency_ms"] = round((time.perf_counter() - db_started) * 1000, 2)
    except Exception:
        health["checks"]["database"]["status"] = "down"
        health["status"] = "degraded"

    if settings.is_deployed_env:
        redis_started = time.perf_counter()
        try:
            from app.core.tasks import get_redis

            redis = await get_redis()
            await redis.ping()
            health["checks"]["redis"] = {
                "status": "up",
                "latency_ms": round((time.perf_counter() - redis_started) * 1000, 2),
            }
        except Exception:
            health["checks"]["redis"] = {"status": "down"}
            health["status"] = "degraded"

    return health


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_logger = logging.getLogger("request")
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        extra = {"request_id": getattr(request.state, "request_id", "unknown")}

        request_logger.info(
            "HTTP %s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra=extra,
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()

    if settings.APP_ENV == "development":
        Base.metadata.create_all(bind=engine)
        initialize_database()
    else:
        # Apply safe additive columns when migrations lag behind models (e.g. jurisdiction_code).
        from app.core.db import ensure_schema_compatibility

        ensure_schema_compatibility()
        if settings.is_deployed_env:
            verify_alembic_at_head(engine)

    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    from app.scheduler import start_scheduler, stop_scheduler

    logger.info(
        "Starting Declairo API lifecycle (env=%s, sentry=%s)",
        settings.APP_ENV,
        "enabled" if settings.SENTRY_DSN else "disabled",
    )
    start_scheduler()

    yield

    stop_scheduler()
    logger.info("Stopped Declairo API lifecycle")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_observability(settings)

    app = FastAPI(
        title="Declairo API",
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    @app.get("/health", tags=["system"])
    async def health_check(db: Session = Depends(get_db)):
        return await _health_payload(db, settings)

    @app.get("/ready", tags=["system"])
    async def readiness_check(db: Session = Depends(get_db)):
        payload = await _health_payload(db, settings)
        return JSONResponse(status_code=200 if payload["status"] == "healthy" else 503, content=payload)

    @app.get("/live", tags=["system"])
    async def liveness_check():
        return {"status": "alive", "version": settings.APP_VERSION}

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning("Validation error: %s", exc, extra={"request_id": getattr(request.state, "request_id", "unknown")})
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error. Please contact support."},
        )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://accounts.google.com https://oauth2.googleapis.com "
            "https://openidconnect.googleapis.com https://github.com https://api.github.com; "
            "frame-ancestors 'none';"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CsrfMiddleware)

    if settings.is_deployed_env:
        app.add_middleware(HTTPSRedirectMiddleware)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Read CORS origins from settings
    origins = settings.cors_origins
    if isinstance(origins, str):
        origins = [o.strip() for o in origins.split(",") if o.strip()]
    else:
        origins = list(origins or [])

    if settings.is_deployed_env and not origins:
        logger.error("CRITICAL: No CORS origins defined outside development")

    # Dev origins always include localhost for local development
    DEV_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    if settings.is_deployed_env:
        allowed_origins = origins if origins else []
    else:
        # In dev: merge env origins + localhost defaults
        allowed_origins = list(set(origins + DEV_ORIGINS))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "X-Requested-With",
            "X-CSRF-Token",
        ],
        expose_headers=["Content-Disposition"],
    )

    app.include_router(api_router, prefix="/api")
    register_v1_aliases(app)

    logger.info(
        "Declairo API configured (env=%s, log_format=%s, sentry=%s)",
        settings.APP_ENV,
        "json" if settings.is_deployed_env else "plain",
        "enabled" if settings.SENTRY_DSN else "disabled",
    )

    if os.getenv("ENABLE_METRICS", "").lower() in ("1", "true", "yes"):
        from prometheus_fastapi_instrumentator import Instrumentator

        Instrumentator().instrument(app).expose(
            app,
            endpoint="/metrics",
            include_in_schema=False,
        )

    return app


app = create_app()

__all__ = ["app", "BACKEND_ROOT", "RUNS_DIR", "create_app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.server:app",
        host=os.getenv("UVICORN_HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("APP_ENV", "development") == "development",
    )
