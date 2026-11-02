"""Verify database schema matches latest Alembic revision (production/staging)."""

from __future__ import annotations

import logging
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def verify_alembic_at_head(engine: Engine) -> None:
    """Raise RuntimeError if alembic_version is missing or not at script head."""
    backend_root = Path(__file__).resolve().parents[2]
    ini = backend_root / "alembic.ini"
    if not ini.exists():
        logger.warning("alembic.ini not found at %s — skipping migration check", ini)
        return

    cfg = Config(str(ini))
    script = ScriptDirectory.from_config(cfg)
    expected = script.get_current_head()
    if not expected:
        raise RuntimeError("Alembic has no revision heads configured")

    with engine.connect() as conn:
        try:
            row = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
        except Exception as e:
            raise RuntimeError(
                "Database is missing alembic_version table. Run `alembic upgrade head` before starting the app."
            ) from e

    current = row[0] if row else None
    if current != expected:
        raise RuntimeError(
            f"Database migration mismatch: database is at {current!r}, "
            f"application expects {expected!r}. Run `alembic upgrade head`."
        )
