"""Add portfolio geo jurisdiction tracking columns.

Revision ID: a3e8f2b1c904
Revises: f8a2b1c9d4e0
Create Date: 2026-05-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3e8f2b1c904"
down_revision: Union[str, Sequence[str], None] = "f8a2b1c9d4e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("portfolios"):
        return

    cols = {c["name"] for c in inspector.get_columns("portfolios")}
    if "geo_jurisdiction_applied" not in cols:
        op.add_column(
            "portfolios",
            sa.Column(
                "geo_jurisdiction_applied",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
    if "country_locked" not in cols:
        op.add_column(
            "portfolios",
            sa.Column(
                "country_locked",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
    if "jurisdiction_source" not in cols:
        op.add_column(
            "portfolios",
            sa.Column("jurisdiction_source", sa.String(length=16), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("portfolios"):
        return
    cols = {c["name"] for c in inspector.get_columns("portfolios")}
    if "jurisdiction_source" in cols:
        op.drop_column("portfolios", "jurisdiction_source")
    if "country_locked" in cols:
        op.drop_column("portfolios", "country_locked")
    if "geo_jurisdiction_applied" in cols:
        op.drop_column("portfolios", "geo_jurisdiction_applied")
