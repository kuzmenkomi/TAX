from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

from app.core.security import encrypt_secret_if_needed

BACKEND_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = BACKEND_ROOT.parent

load_dotenv(WORKSPACE_ROOT / ".env", override=False)
load_dotenv(BACKEND_ROOT / ".env", override=False)

from .base import Base  # noqa: E402 — after dotenv so DATABASE_URL is loaded before engine import chain


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    return "sqlite:///./tax_app.db"


DATABASE_URL = _get_database_url()

# Optimize engine based on database type
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # :memory: must use StaticPool so create_all and sessions share one DB.
    if ":memory:" in DATABASE_URL:
        engine = create_engine(
            DATABASE_URL,
            future=True,
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    else:
        engine = create_engine(
            DATABASE_URL,
            future=True,
            echo=False,
            poolclass=NullPool,
            connect_args={"timeout": 30},
        )
else:
    # PostgreSQL: Use QueuePool for connection pooling
    pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "40"))
    pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    engine = create_engine(
        DATABASE_URL,
        future=True,
        echo=False,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=pool_recycle,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def _table_exists(conn, table_name: str, dialect: str) -> bool:
    if dialect == "sqlite":
        row = conn.exec_driver_sql(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            """,
            (table_name,),
        ).fetchone()
        return row is not None
    row = conn.exec_driver_sql(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def _existing_columns(conn, table_name: str, dialect: str) -> set[str]:
    if dialect == "sqlite":
        return {
            row[1]
            for row in conn.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
        }
    rows = conn.exec_driver_sql(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        """,
        (table_name,),
    ).fetchall()
    return {row[0] for row in rows}


def _add_column_if_missing(
    conn,
    table_name: str,
    column_name: str,
    *,
    sqlite_ddl: str,
    postgres_ddl: str,
    dialect: str,
    existing: set[str],
) -> None:
    if column_name in existing:
        return
    ddl = sqlite_ddl if dialect == "sqlite" else postgres_ddl
    if dialect == "postgresql":
        conn.exec_driver_sql(
            f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {ddl}"
        )
    else:
        conn.exec_driver_sql(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"
        )


def ensure_schema_compatibility() -> None:
    """
    Add columns missing from older DB files (create_all does not ALTER existing tables).
    Safe on SQLite dev DBs and as a fallback when Alembic was not run yet.
    """
    dialect = engine.dialect.name
    if dialect not in ("sqlite", "postgresql"):
        return

    # (column_name, sqlite_ddl, postgres_ddl)
    additive_columns: dict[str, list[tuple[str, str, str]]] = {
        "users": [
            ("full_name", "VARCHAR(255)", "VARCHAR(255)"),
            ("avatar_url", "TEXT", "TEXT"),
            ("oauth_provider", "VARCHAR(50)", "VARCHAR(50)"),
            ("oauth_provider_id", "VARCHAR(255)", "VARCHAR(255)"),
            ("role", "VARCHAR(32) NOT NULL DEFAULT 'user'", "VARCHAR(32) NOT NULL DEFAULT 'user'"),
            ("totp_secret_encrypted", "TEXT", "TEXT"),
            ("totp_pending", "INTEGER NOT NULL DEFAULT 0", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("totp_enabled", "INTEGER NOT NULL DEFAULT 0", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("totp_confirmed_at", "DATETIME", "TIMESTAMP WITH TIME ZONE"),
            ("allow_support_until", "DATETIME", "TIMESTAMP WITH TIME ZONE"),
            ("jurisdiction_code", "VARCHAR(2) NOT NULL DEFAULT 'BR'", "VARCHAR(2) NOT NULL DEFAULT 'BR'"),
        ],
        "portfolios": [
            ("geo_jurisdiction_applied", "INTEGER NOT NULL DEFAULT 0", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("country_locked", "INTEGER NOT NULL DEFAULT 0", "BOOLEAN NOT NULL DEFAULT FALSE"),
            ("jurisdiction_source", "VARCHAR(16)", "VARCHAR(16)"),
        ],
        "exchange_connections": [
            ("exchange_name", "VARCHAR(64)", "VARCHAR(64)"),
            ("api_key", "VARCHAR(512)", "VARCHAR(512)"),
            ("api_secret", "VARCHAR(512)", "VARCHAR(512)"),
            ("passphrase", "VARCHAR(512)", "VARCHAR(512)"),
            ("last_error", "TEXT", "TEXT"),
            ("updated_at", "DATETIME", "TIMESTAMP WITH TIME ZONE"),
        ],
        "wallet_connections": [
            ("updated_at", "DATETIME", "TIMESTAMP WITH TIME ZONE"),
        ],
        "sync_jobs": [
            ("job_type", "VARCHAR(64)", "VARCHAR(64)"),
            ("source", "VARCHAR(255)", "VARCHAR(255)"),
            ("transaction_count", "INTEGER DEFAULT 0", "INTEGER DEFAULT 0"),
            ("result", "TEXT", "TEXT"),
        ],
    }

    with engine.begin() as conn:
        for table_name, columns in additive_columns.items():
            if not _table_exists(conn, table_name, dialect):
                continue
            existing = _existing_columns(conn, table_name, dialect)
            for column_name, sqlite_ddl, postgres_ddl in columns:
                _add_column_if_missing(
                    conn,
                    table_name,
                    column_name,
                    sqlite_ddl=sqlite_ddl,
                    postgres_ddl=postgres_ddl,
                    dialect=dialect,
                    existing=existing,
                )
                existing.add(column_name)


def migrate_encrypted_exchange_credentials() -> None:
    with engine.begin() as conn:
        has_exchange_table = conn.exec_driver_sql(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'exchange_connections'
            """
        ).fetchone()
        if not has_exchange_table:
            return

        rows = conn.exec_driver_sql(
            """
            SELECT id, api_key, api_secret, passphrase
            FROM exchange_connections
            WHERE api_key IS NOT NULL OR api_secret IS NOT NULL OR passphrase IS NOT NULL
            """
        ).fetchall()

        for row in rows:
            conn.exec_driver_sql(
                """
                UPDATE exchange_connections
                SET api_key = ?, api_secret = ?, passphrase = ?
                WHERE id = ?
                """,
                (
                    encrypt_secret_if_needed(row[1]),
                    encrypt_secret_if_needed(row[2]),
                    encrypt_secret_if_needed(row[3]),
                    row[0],
                ),
            )


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()
    migrate_encrypted_exchange_credentials()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



__all__ = ["Base", "SessionLocal", "engine", "get_db", "initialize_database"]
