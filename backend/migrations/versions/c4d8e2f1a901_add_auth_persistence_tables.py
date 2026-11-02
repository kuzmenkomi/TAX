"""Add auth and billing persistence tables missing from clean PostgreSQL migrations.

Revision ID: c4d8e2f1a901
Revises: b9f7c1a4de22
Create Date: 2026-04-26 22:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4d8e2f1a901"
down_revision: Union[str, Sequence[str], None] = "b9f7c1a4de22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return inspector.has_table(table_name)


def upgrade() -> None:
    if not _has_table("refresh_tokens"):
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token", sa.String(length=512), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token"),
        )
        op.create_index(op.f("ix_refresh_tokens_id"), "refresh_tokens", ["id"], unique=False)
        op.create_index(op.f("ix_refresh_tokens_token"), "refresh_tokens", ["token"], unique=True)

    if not _has_table("subscriptions"):
        op.create_table(
            "subscriptions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
            sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
            sa.Column("plan", sa.String(length=32), nullable=False, server_default="free"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("current_period_end", sa.DateTime(), nullable=True),
            sa.Column("transaction_count", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index(op.f("ix_subscriptions_id"), "subscriptions", ["id"], unique=False)
        op.create_index(op.f("ix_subscriptions_user_id"), "subscriptions", ["user_id"], unique=True)
        op.create_index(
            op.f("ix_subscriptions_stripe_customer_id"),
            "subscriptions",
            ["stripe_customer_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_subscriptions_stripe_subscription_id"),
            "subscriptions",
            ["stripe_subscription_id"],
            unique=False,
        )


def downgrade() -> None:
    if _has_table("subscriptions"):
        op.drop_index(op.f("ix_subscriptions_stripe_subscription_id"), table_name="subscriptions")
        op.drop_index(op.f("ix_subscriptions_stripe_customer_id"), table_name="subscriptions")
        op.drop_index(op.f("ix_subscriptions_user_id"), table_name="subscriptions")
        op.drop_index(op.f("ix_subscriptions_id"), table_name="subscriptions")
        op.drop_table("subscriptions")

    if _has_table("refresh_tokens"):
        op.drop_index(op.f("ix_refresh_tokens_token"), table_name="refresh_tokens")
        op.drop_index(op.f("ix_refresh_tokens_id"), table_name="refresh_tokens")
        op.drop_table("refresh_tokens")
