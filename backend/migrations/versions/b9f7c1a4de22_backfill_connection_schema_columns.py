"""Backfill missing connection-related columns for PostgreSQL deployments.

Revision ID: b9f7c1a4de22
Revises: e4c3cbddcea6
Create Date: 2026-04-26 22:05:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b9f7c1a4de22"
down_revision: Union[str, Sequence[str], None] = "e4c3cbddcea6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if column.name not in _column_names(table_name):
        op.add_column(table_name, column)


def _drop_column_if_present(table_name: str, column_name: str) -> None:
    if column_name in _column_names(table_name):
        op.drop_column(table_name, column_name)


def upgrade() -> None:
    _add_column_if_missing(
        "exchange_connections",
        sa.Column("exchange_name", sa.String(length=64), nullable=True),
    )

    _add_column_if_missing(
        "wallet_connections",
        sa.Column("sync_status", sa.String(length=32), nullable=False, server_default="idle"),
    )
    _add_column_if_missing(
        "wallet_connections",
        sa.Column("auto_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    _add_column_if_missing(
        "wallet_connections",
        sa.Column("sync_interval_hours", sa.Integer(), nullable=False, server_default="6"),
    )
    _add_column_if_missing(
        "wallet_connections",
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
    )
    _add_column_if_missing(
        "wallet_connections",
        sa.Column("next_sync_at", sa.DateTime(), nullable=True),
    )
    _add_column_if_missing(
        "wallet_connections",
        sa.Column("last_block_synced", sa.String(length=128), nullable=True),
    )
    _add_column_if_missing(
        "wallet_connections",
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    _add_column_if_missing(
        "wallet_connections",
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    _add_column_if_missing(
        "sync_jobs",
        sa.Column("job_type", sa.String(length=64), nullable=True),
    )
    _add_column_if_missing(
        "sync_jobs",
        sa.Column("source", sa.String(length=255), nullable=True),
    )
    _add_column_if_missing(
        "sync_jobs",
        sa.Column("transaction_count", sa.Integer(), nullable=True, server_default="0"),
    )
    _add_column_if_missing(
        "sync_jobs",
        sa.Column("result", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    _drop_column_if_present("sync_jobs", "result")
    _drop_column_if_present("sync_jobs", "transaction_count")
    _drop_column_if_present("sync_jobs", "source")
    _drop_column_if_present("sync_jobs", "job_type")

    _drop_column_if_present("wallet_connections", "updated_at")
    _drop_column_if_present("wallet_connections", "last_error")
    _drop_column_if_present("wallet_connections", "last_block_synced")
    _drop_column_if_present("wallet_connections", "next_sync_at")
    _drop_column_if_present("wallet_connections", "last_synced_at")
    _drop_column_if_present("wallet_connections", "sync_interval_hours")
    _drop_column_if_present("wallet_connections", "auto_sync_enabled")
    _drop_column_if_present("wallet_connections", "sync_status")

    _drop_column_if_present("exchange_connections", "exchange_name")
