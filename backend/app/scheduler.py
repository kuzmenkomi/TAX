"""Background task scheduler helpers."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.core.db import engine
from app.db import SessionLocal
from app.models import ExchangeConnection, WalletConnection
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)

_SCHEDULER_LOCK_KEY = 22042601
_scheduler: BackgroundScheduler | None = None
_scheduler_lock_conn: Any | None = None
_scheduler_state_lock = Lock()


def _create_scheduler() -> BackgroundScheduler:
    """Create and configure the APScheduler instance."""
    settings = get_settings()
    if settings.is_postgresql:
        from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

        jobstores = {
            "default": SQLAlchemyJobStore(engine=engine, tablename="apscheduler_jobs"),
        }
    else:
        jobstores = {"default": MemoryJobStore()}

    executors = {"default": ThreadPoolExecutor(max_workers=4)}
    job_defaults = {
        "coalesce": True,
        "max_instances": 1,
        "misfire_grace_time": 300,
    }
    return BackgroundScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone="UTC",
    )


def _acquire_scheduler_lock() -> bool:
    """Elect a single scheduler leader in multi-worker PostgreSQL deployments."""
    global _scheduler_lock_conn

    settings = get_settings()
    if not settings.is_deployed_env or not settings.is_postgresql:
        return True

    if _scheduler_lock_conn is not None:
        return True

    conn = None
    try:
        conn = engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT pg_try_advisory_lock(%s)", (_SCHEDULER_LOCK_KEY,))
        row = cursor.fetchone()
        cursor.close()
        lock_acquired = bool(row and row[0])
        if not lock_acquired:
            conn.close()
            logger.info("Scheduler lock is held by another process; skipping local scheduler startup")
            return False

        _scheduler_lock_conn = conn
        logger.info("Acquired PostgreSQL advisory lock for scheduler leadership")
        return True
    except Exception:
        logger.exception("Failed to acquire PostgreSQL advisory lock for scheduler startup")
        if conn is not None:
            try:
                conn.close()
            except Exception:
                logger.debug("Failed to close scheduler advisory-lock connection", exc_info=True)
        return False


def _release_scheduler_lock() -> None:
    """Release the leader lock when this process stops owning the scheduler."""
    global _scheduler_lock_conn

    if _scheduler_lock_conn is None:
        return

    try:
        cursor = _scheduler_lock_conn.cursor()
        cursor.execute("SELECT pg_advisory_unlock(%s)", (_SCHEDULER_LOCK_KEY,))
        cursor.close()
    except Exception:
        logger.warning("Failed to release PostgreSQL advisory lock for scheduler", exc_info=True)
    finally:
        try:
            _scheduler_lock_conn.close()
        except Exception:
            logger.debug("Failed to close scheduler advisory-lock connection", exc_info=True)
        _scheduler_lock_conn = None


def _register_jobs(scheduler: BackgroundScheduler) -> None:
    """Register periodic jobs in an idempotent way."""
    scheduler.add_job(
        _monitor_due_syncs,
        "interval",
        minutes=10,
        id="monitor_due_syncs",
        name="Monitor connections due for sync",
        next_run_time=datetime.now(timezone.utc) + timedelta(seconds=30),
        replace_existing=True,
    )
    scheduler.add_job(
        _run_price_update,
        "interval",
        minutes=15,
        id="price_update",
        name="Update asset prices",
        replace_existing=True,
    )


def start_scheduler() -> None:
    """Start the background scheduler from the app lifespan."""
    global _scheduler

    with _scheduler_state_lock:
        if _scheduler is not None and _scheduler.running:
            logger.info("Scheduler is already running in this process")
            return

        if not _acquire_scheduler_lock():
            return

        scheduler = _create_scheduler()
        try:
            _register_jobs(scheduler)
            scheduler.start()
        except Exception:
            logger.exception("Failed to start background scheduler")
            try:
                scheduler.shutdown(wait=False)
            except Exception:
                logger.debug("Scheduler shutdown after failed startup also failed", exc_info=True)
            _release_scheduler_lock()
            raise

        _scheduler = scheduler
        logger.info("Background scheduler started with %d jobs", len(_scheduler.get_jobs()))


def stop_scheduler() -> None:
    """Gracefully stop the scheduler and release leadership if held."""
    global _scheduler

    with _scheduler_state_lock:
        if _scheduler is not None and _scheduler.running:
            _scheduler.shutdown(wait=False)
            logger.info("Background scheduler stopped")
        _scheduler = None
        _release_scheduler_lock()


def get_sync_status() -> dict[str, Any]:
    """Return scheduler state and current jobs."""
    if _scheduler is None or not _scheduler.running:
        return {"scheduler_running": False, "jobs": []}

    jobs = [
        {
            "id": job.id,
            "name": job.name or job.id,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
        }
        for job in _scheduler.get_jobs()
    ]
    return {"scheduler_running": True, "jobs": jobs}


def sync_all_wallets() -> dict[str, Any]:
    """Manually trigger sync for all auto-sync-enabled wallets."""
    db = SessionLocal()
    try:
        wallets = db.query(WalletConnection).filter(
            WalletConnection.auto_sync_enabled.is_(True),
            WalletConnection.sync_status != "syncing",
        ).all()

        if not wallets:
            return {"status": "ok", "message": "No wallets to sync", "synced": 0}

        results = []
        for wallet in wallets:
            try:
                result = SyncService.sync_wallet(wallet.id)
                results.append({"wallet_id": wallet.id, **result})
            except Exception as exc:
                logger.error("Wallet sync error (id=%s): %s", wallet.id, exc)
                results.append({"wallet_id": wallet.id, "status": "error", "message": str(exc)})

        return {
            "status": "ok",
            "synced": sum(1 for result in results if result.get("status") == "success"),
            "total": len(results),
            "results": results,
        }
    finally:
        db.close()


def sync_all_exchanges() -> dict[str, Any]:
    """Manually trigger sync for all auto-sync-enabled exchanges."""
    db = SessionLocal()
    try:
        exchanges = db.query(ExchangeConnection).filter(
            ExchangeConnection.auto_sync_enabled.is_(True),
            ExchangeConnection.sync_status != "syncing",
        ).all()

        if not exchanges:
            return {"status": "ok", "message": "No exchanges to sync", "synced": 0}

        results = []
        for exchange in exchanges:
            try:
                result = SyncService.sync_exchange(exchange.id)
                results.append({"exchange_id": exchange.id, **result})
            except Exception as exc:
                logger.error("Exchange sync error (id=%s): %s", exchange.id, exc)
                results.append({"exchange_id": exchange.id, "status": "error", "message": str(exc)})

        return {
            "status": "ok",
            "synced": sum(1 for result in results if result.get("status") == "success"),
            "total": len(results),
            "results": results,
        }
    finally:
        db.close()


def update_prices() -> dict[str, Any]:
    """Refresh latest asset prices."""
    try:
        _run_price_update()
        return {"status": "ok", "message": "Price update completed"}
    except Exception as exc:
        logger.error("Price update error: %s", exc)
        return {"status": "error", "message": str(exc)}


def manual_sync_wallet(wallet_id: int) -> dict[str, Any]:
    """Manually sync a single wallet."""
    try:
        return SyncService.sync_wallet(wallet_id)
    except Exception as exc:
        logger.error("Manual wallet sync error (id=%s): %s", wallet_id, exc)
        return {"status": "error", "message": str(exc)}


def trigger_recalculation(user_id: int) -> None:
    """Trigger a best-effort recalculation job for a user."""
    logger.info("Recalculation triggered for user %s", user_id)
    if _scheduler is not None and _scheduler.running:
        _scheduler.add_job(
            _recalculate_user,
            args=[user_id],
            id=f"recalc_user_{user_id}",
            name=f"Recalculate user {user_id}",
            replace_existing=True,
        )


def _monitor_due_syncs() -> None:
    """Scan for wallet and exchange connections that are due for sync."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        due_wallets = db.query(WalletConnection).filter(
            WalletConnection.auto_sync_enabled.is_(True),
            WalletConnection.sync_status != "syncing",
            WalletConnection.next_sync_at <= now,
        ).all()
        for wallet in due_wallets:
            logger.info("Auto-syncing wallet %s (due at %s)", wallet.id, wallet.next_sync_at)
            try:
                SyncService.sync_wallet(wallet.id)
            except Exception as exc:
                logger.error("Auto-sync wallet error (id=%s): %s", wallet.id, exc)

        due_exchanges = db.query(ExchangeConnection).filter(
            ExchangeConnection.auto_sync_enabled.is_(True),
            ExchangeConnection.sync_status != "syncing",
            ExchangeConnection.next_sync_at <= now,
        ).all()
        for exchange in due_exchanges:
            logger.info("Auto-syncing exchange %s (due at %s)", exchange.id, exchange.next_sync_at)
            try:
                SyncService.sync_exchange(exchange.id)
            except Exception as exc:
                logger.error("Auto-sync exchange error (id=%s): %s", exchange.id, exc)

        dispatched = len(due_wallets) + len(due_exchanges)
        if dispatched:
            logger.info("Monitor scan complete: dispatched %d sync jobs", dispatched)
    except Exception as exc:
        logger.error("Monitor scan error: %s", exc)
    finally:
        db.close()


def _run_price_update() -> None:
    """Fetch latest prices for tracked assets."""
    try:
        from app.accounting.pricing import PriceService

        price_service = PriceService()
        price_service.update_cache()
        logger.info("Price cache updated successfully")
    except ImportError:
        logger.warning("PriceService not available; skipping price update")
    except Exception as exc:
        logger.error("Price update failed: %s", exc)


def _recalculate_user(user_id: int) -> None:
    """Placeholder recalculation hook used after reconciliation changes."""
    logger.info("Running recalculation for user %s", user_id)
