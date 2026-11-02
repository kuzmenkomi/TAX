"""Add jurisdiction_code to users.

Revision ID: b7c4e9a2f105
Revises: a3e8f2b1c904
Create Date: 2026-05-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c4e9a2f105"
down_revision: Union[str, Sequence[str], None] = "a3e8f2b1c904"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return
    cols = {c["name"] for c in inspector.get_columns("users")}
    if "jurisdiction_code" not in cols:
        op.add_column(
            "users",
            sa.Column(
                "jurisdiction_code",
                sa.String(length=2),
                nullable=False,
                server_default="BR",
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return
    cols = {c["name"] for c in inspector.get_columns("users")}
    if "jurisdiction_code" in cols:
        op.drop_column("users", "jurisdiction_code")
