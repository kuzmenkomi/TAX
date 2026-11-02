import asyncio
import logging
import os

from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.observability import setup_observability
from app.services.task_manager import TaskManager

logger = logging.getLogger(__name__)
settings = get_settings()
setup_observability(settings)


def _redis_password() -> str | None:
    pwd = (settings.REDIS_PASSWORD or os.getenv("REDIS_PASSWORD") or "").strip() or None
    if settings.is_deployed_env and not pwd:
        raise RuntimeError("REDIS_PASSWORD must be set outside development for workers")
    return pwd


async def run_analysis_task(ctx, task_id: str, file_bytes: bytes, user_id: int, filename: str, **kwargs):
    """Background worker task to run the tax analysis."""
    logger.info("Worker: Starting task %s for user %s", task_id, user_id)
    manager = TaskManager()

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: manager.run_analysis(
            task_id,
            file_bytes,
            user_id,
            filename,
            db_factory=SessionLocal,
            **kwargs,
        ),
    )
    logger.info("Worker: Task %s complete", task_id)


async def run_export_task(ctx, task_id: str, format: str, run_id: int, user_id: int, **kwargs):
    """Background worker task to run the tax report export."""
    logger.info("Worker: Starting export task %s for user %s", task_id, user_id)
    from app.routers.v1.exports import run_export_bg_task
    import asyncio

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: run_export_bg_task(task_id, format, run_id, user_id)
    )
    logger.info("Worker: Export task %s complete", task_id)


async def startup(ctx):
    logger.info(
        "Worker starting up (env=%s, sentry=%s)",
        settings.APP_ENV,
        "enabled" if settings.SENTRY_DSN else "disabled",
    )


async def shutdown(ctx):
    logger.info("Worker shutting down...")


class WorkerSettings:
    """Arq worker settings."""

    functions = [run_analysis_task, run_export_task]
    redis_settings = RedisSettings(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=_redis_password(),
    )
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 600

