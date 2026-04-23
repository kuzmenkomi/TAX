from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from app.core.security import encrypt_secret_if_needed

BACKEND_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = BACKEND_ROOT.parent

load_dotenv(WORKSPACE_ROOT / ".env", override=False)
load_dotenv(BACKEND_ROOT / ".env", override=False)


class Base(DeclarativeBase):
    pass


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    return "sqlite:///./tax_app.db"


DATABASE_URL = _get_database_url()

# Optimize engine based on database type
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # SQLite: Use NullPool (no connection pooling needed)
    engine = create_engine(
        DATABASE_URL,
        future=True,
        echo=False,
        poolclass=NullPool,
        connect_args={"timeout": 30}
    )
else:
    # PostgreSQL: Use QueuePool for connection pooling
    engine = create_engine(
        DATABASE_URL,
        future=True,
        echo=False,
        poolclass=QueuePool,
        pool_size=20,           # Number of connections to keep in pool
        max_overflow=40,        # Additional connections beyond pool_size
        pool_pre_ping=True,     # Test connection before using (detects stale connections)
        pool_recycle=3600,      # Recycle connections after 1 hour
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def ensure_schema_compatibility() -> None:
    if engine.dialect.name != "sqlite":
        return

    compat_columns = {
        "exchange_connections": {
            "exchange_name": "VARCHAR(64)",
            "api_key": "VARCHAR(512)",
            "api_secret": "VARCHAR(512)",
            "passphrase": "VARCHAR(512)",
            "last_error": "TEXT",
            "updated_at": "DATETIME",
        },
        "wallet_connections": {
            "updated_at": "DATETIME",
        },
        "sync_jobs": {
            "job_type": "VARCHAR(64)",
            "source": "VARCHAR(255)",
            "transaction_count": "INTEGER DEFAULT 0",
            "result": "TEXT",
        },
    }

    with engine.begin() as conn:
        for table_name, columns in compat_columns.items():
            table_exists = conn.exec_driver_sql(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = ?
                """,
                (table_name,),
            ).fetchone()
            if not table_exists:
                continue

            existing = {
                row[1]
                for row in conn.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
            }
            for column_name, column_ddl in columns.items():
                if column_name in existing:
                    continue
                conn.exec_driver_sql(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_ddl}"
                )


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
    ensure_schema_compatibility()
    migrate_encrypted_exchange_credentials()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



__all__ = ["Base", "SessionLocal", "engine", "get_db", "initialize_database"]
