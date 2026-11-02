import os
from arq import create_pool
from arq.connections import RedisSettings

_redis = None


def _redis_password() -> str | None:
    """Redis AUTH password; required in production."""
    from app.core.config import get_settings

    s = get_settings()
    pwd = (s.REDIS_PASSWORD or os.getenv("REDIS_PASSWORD") or "").strip() or None
    if s.is_deployed_env and not pwd:
        raise RuntimeError("REDIS_PASSWORD must be set outside development for Redis clients")
    return pwd


async def get_redis():
    """
    Singleton-like access to the arq redis pool.
    """
    global _redis
    if _redis is None:
        _redis = await create_pool(
            RedisSettings(
                host=os.getenv("REDIS_HOST", "redis"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=_redis_password(),
            )
        )
    return _redis

async def enqueue_analysis(task_id: str, file_bytes: bytes, user_id: int, filename: str, **kwargs):
    """
    Enqueue an analysis task to the arq worker.
    """
    redis = await get_redis()
    await redis.enqueue_job(
        'run_analysis_task',
        task_id=task_id,
        file_bytes=file_bytes,
        user_id=user_id,
        filename=filename,
        **kwargs
    )


async def enqueue_export(task_id: str, format: str, run_id: int, user_id: int):
    """
    Enqueue an export task to the arq worker.
    """
    redis = await get_redis()
    await redis.enqueue_job(
        'run_export_task',
        task_id=task_id,
        format=format,
        run_id=run_id,
        user_id=user_id
    )

