"""Add TOTP 2FA columns, user roles, and support impersonation audit log.

Revision ID: f8a2b1c9d4e0
Revises: 181177ded9f6
Create Date: 2026-05-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8a2b1c9d4e0"
down_revision: Union[str, Sequence[str], None] = "181177ded9f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_cols = {c["name"] for c in inspector.get_columns("users")} if inspector.has_table("users") else set()
    if "role" not in user_cols:
        op.add_column(
            "users",
            sa.Column("role", sa.String(length=32), nullable=False, server_default="user"),
        )
    if "totp_secret_encrypted" not in user_cols:
        op.add_column("users", sa.Column("totp_secret_encrypted", sa.Text(), nullable=True))
    if "totp_pending" not in user_cols:
        op.add_column(
            "users",
            sa.Column("totp_pending", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if "totp_enabled" not in user_cols:
        op.add_column(
            "users",
            sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if "totp_confirmed_at" not in user_cols:
        op.add_column("users", sa.Column("totp_confirmed_at", sa.DateTime(), nullable=True))

    if not inspector.has_table("support_impersonation_logs"):
        op.create_table(
            "support_impersonation_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("actor_user_id", sa.Integer(), nullable=False),
            sa.Column("subject_user_id", sa.Integer(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("ended_at", sa.DateTime(), nullable=True),
            sa.Column("actor_ip", sa.String(length=64), nullable=True),
            sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["subject_user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_support_impersonation_logs_id"),
            "support_impersonation_logs",
            ["id"],
            unique=False,
        )
        op.create_index(
            "ix_support_imp_actor",
            "support_impersonation_logs",
            ["actor_user_id"],
            unique=False,
        )
        op.create_index(
            "ix_support_imp_subject",
            "support_impersonation_logs",
            ["subject_user_id"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("ix_support_imp_subject", table_name="support_impersonation_logs")
    op.drop_index("ix_support_imp_actor", table_name="support_impersonation_logs")
    op.drop_index(op.f("ix_support_impersonation_logs_id"), table_name="support_impersonation_logs")
    op.drop_table("support_impersonation_logs")

    op.drop_column("users", "totp_confirmed_at")
    op.drop_column("users", "totp_enabled")
    op.drop_column("users", "totp_pending")
    op.drop_column("users", "totp_secret_encrypted")
    op.drop_column("users", "role")
