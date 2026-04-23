"""Add OAuth fields to ExchangeConnection

Revision ID: 1d66753f2577
Revises: 181177ded9f6
Create Date: 2026-04-22 14:42:31.182694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.models.types


# revision identifiers, used by Alembic.
revision: str = '1d66753f2577'
down_revision: Union[str, Sequence[str], None] = '181177ded9f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adding columns missing in DB but present in model
    op.add_column('exchange_connections', sa.Column('api_key', app.models.types.EncryptedString(length=512), nullable=True))
    op.add_column('exchange_connections', sa.Column('api_secret', app.models.types.EncryptedString(length=512), nullable=True))
    op.add_column('exchange_connections', sa.Column('passphrase', app.models.types.EncryptedString(length=512), nullable=True))
    op.add_column('exchange_connections', sa.Column('sync_status', sa.String(length=32), nullable=False, server_default='idle'))
    op.add_column('exchange_connections', sa.Column('auto_sync_enabled', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('exchange_connections', sa.Column('sync_interval_hours', sa.Integer(), nullable=False, server_default='4'))
    op.add_column('exchange_connections', sa.Column('last_synced_at', sa.DateTime(), nullable=True))
    op.add_column('exchange_connections', sa.Column('next_sync_at', sa.DateTime(), nullable=True))
    op.add_column('exchange_connections', sa.Column('last_error', sa.Text(), nullable=True))
    op.add_column('exchange_connections', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Adding OAuth specific columns
    op.add_column('exchange_connections', sa.Column('is_oauth', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('exchange_connections', sa.Column('oauth_expires_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('exchange_connections', 'oauth_expires_at')
    op.drop_column('exchange_connections', 'is_oauth')
    op.drop_column('exchange_connections', 'updated_at')
    op.drop_column('exchange_connections', 'last_error')
    op.drop_column('exchange_connections', 'next_sync_at')
    op.drop_column('exchange_connections', 'last_synced_at')
    op.drop_column('exchange_connections', 'sync_interval_hours')
    op.drop_column('exchange_connections', 'auto_sync_enabled')
    op.drop_column('exchange_connections', 'sync_status')
    op.drop_column('exchange_connections', 'passphrase')
    op.drop_column('exchange_connections', 'api_secret')
    op.drop_column('exchange_connections', 'api_key')
