"""Background scheduling is idempotent and isolates per-account outages."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app import scheduler


def test_scheduler_start_is_idempotent_and_stop_releases_state(monkeypatch):
    fake = Mock(running=False)
    fake.get_jobs.return_value = []
    fake.start.side_effect = lambda: setattr(fake, "running", True)
    monkeypatch.setattr(scheduler, "_scheduler", None)
    monkeypatch.setattr(scheduler, "_create_scheduler", lambda: fake)
    monkeypatch.setattr(scheduler, "_acquire_scheduler_lock", lambda: True)
    release = Mock()
    monkeypatch.setattr(scheduler, "_release_scheduler_lock", release)
    scheduler.start_scheduler()
    scheduler.start_scheduler()
    fake.start.assert_called_once()
    assert fake.add_job.call_count == 2
    assert scheduler.get_sync_status()["scheduler_running"] is True
    scheduler.stop_scheduler()
    fake.shutdown.assert_called_once_with(wait=False)
    assert scheduler.get_sync_status()["scheduler_running"] is False
    release.assert_called_once()


def test_scheduler_start_failure_closes_resources(monkeypatch):
    fake = Mock()
    fake.start.side_effect = RuntimeError("cannot start")
    monkeypatch.setattr(scheduler, "_scheduler", None)
    monkeypatch.setattr(scheduler, "_create_scheduler", lambda: fake)
    monkeypatch.setattr(scheduler, "_acquire_scheduler_lock", lambda: True)
    release = Mock()
    monkeypatch.setattr(scheduler, "_release_scheduler_lock", release)
    with pytest.raises(RuntimeError, match="cannot start"):
        scheduler.start_scheduler()
    fake.shutdown.assert_called_once_with(wait=False)
    release.assert_called_once()


@pytest.mark.parametrize("kind", ["wallet", "exchange"])
def test_one_failed_sync_does_not_block_other_accounts(monkeypatch, kind):
    session = Mock()
    session.query.return_value.filter.return_value.all.return_value = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: session)
    sync = Mock(side_effect=[RuntimeError("offline"), {"status": "success"}])
    monkeypatch.setattr(scheduler.SyncService, f"sync_{kind}", sync)
    result = scheduler.sync_all_wallets() if kind == "wallet" else scheduler.sync_all_exchanges()
    assert result["synced"] == 1 and result["total"] == 2
    assert result["results"][0]["status"] == "error"
    assert sync.call_count == 2
    session.close.assert_called_once()


def test_advisory_lock_is_released_and_connection_closed(monkeypatch):
    connection = Mock()
    connection.cursor.return_value.fetchone.return_value = (True,)
    monkeypatch.setattr(scheduler, "get_settings", lambda: SimpleNamespace(is_deployed_env=True, is_postgresql=True))
    monkeypatch.setattr(scheduler, "engine", SimpleNamespace(raw_connection=lambda: connection))
    monkeypatch.setattr(scheduler, "_scheduler_lock_conn", None)
    assert scheduler._acquire_scheduler_lock() is True
    assert scheduler._acquire_scheduler_lock() is True
    scheduler._release_scheduler_lock()
    connection.close.assert_called_once()
    assert scheduler._scheduler_lock_conn is None


def test_empty_syncs_close_database_sessions(monkeypatch):
    session = Mock()
    session.query.return_value.filter.return_value.all.return_value = []
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: session)
    assert scheduler.sync_all_wallets()["synced"] == 0
    assert scheduler.sync_all_exchanges()["synced"] == 0
    scheduler._monitor_due_syncs()
    assert session.close.call_count == 3
