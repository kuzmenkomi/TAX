"""
Initial TLH and Banking schema

Revision ID: initial_tlh_banking
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial_tlh_banking'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TLH Opportunities table
    op.create_table(
        'tlh_opportunities',
        sa.Column('id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('position_id', sa.String(100), nullable=False),
        sa.Column('asset', sa.String(20), nullable=False),
        sa.Column('loss_amount', sa.Numeric(20, 8), nullable=False),
        sa.Column('tax_rate', sa.Float(), nullable=False),
        sa.Column('priority_score', sa.Float(), nullable=False),
        sa.Column('priority_breakdown', sa.JSON(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('execution_strategy', sa.String(20), nullable=True),
        sa.Column('execution_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_execution_error', sa.String(500), nullable=True),
        sa.Column('dry_run_result', sa.JSON(), nullable=True),
        sa.Column('order_id', sa.String(100), nullable=True),
        sa.Column('quantity_executed', sa.Numeric(20, 8), nullable=True),
        sa.Column('average_price_executed', sa.Numeric(20, 8), nullable=True),
        sa.Column('fees_paid', sa.Numeric(20, 8), nullable=True),
        sa.Column('wash_sale_risk', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('wash_sale_days_remaining', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tlh_user_asset', 'tlh_opportunities', ['user_id', 'asset'])
    op.create_index('ix_tlh_status', 'tlh_opportunities', ['status'])
    op.create_index('ix_tlh_created', 'tlh_opportunities', ['created_at'])

    # TLH Execution History table
    op.create_table(
        'tlh_execution_history',
        sa.Column('id', sa.String(100), nullable=False),
        sa.Column('opportunity_id', sa.String(100), nullable=False),
        sa.Column('strategy', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('dry_run', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('order_id', sa.String(100), nullable=True),
        sa.Column('quantity_executed', sa.Numeric(20, 8), nullable=True),
        sa.Column('average_price', sa.Numeric(20, 8), nullable=True),
        sa.Column('fees_paid', sa.Numeric(20, 8), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('exchange_response', sa.JSON(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['opportunity_id'], ['tlh_opportunities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_exec_opportunity', 'tlh_execution_history', ['opportunity_id'])
    op.create_index('ix_exec_timestamp', 'tlh_execution_history', ['executed_at'])

    # Bank Accounts table
    op.create_table(
        'bank_accounts',
        sa.Column('id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('bank_type', sa.String(50), nullable=False),
        sa.Column('account_number', sa.String(100), nullable=False),
        sa.Column('account_name', sa.String(200), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False),
        sa.Column('balance', sa.Numeric(20, 8), nullable=False),
        sa.Column('api_key', sa.String(500), nullable=True),
        sa.Column('api_secret', sa.String(500), nullable=True),
        sa.Column('refresh_token', sa.String(500), nullable=True),
        sa.Column('sync_status', sa.String(20), nullable=False),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('connected_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bank_user', 'bank_accounts', ['user_id'])
    op.create_index('ix_bank_status', 'bank_accounts', ['sync_status'])

    # Bank Transactions table
    op.create_table(
        'bank_transactions',
        sa.Column('id', sa.String(100), nullable=False),
        sa.Column('account_id', sa.String(100), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(20, 8), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('counterparty', sa.String(200), nullable=False),
        sa.Column('balance_after', sa.Numeric(20, 8), nullable=True),
        sa.Column('matched_crypto_transaction_id', sa.String(100), nullable=True, index=True),
        sa.Column('matched_confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['bank_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bank_txn_account', 'bank_transactions', ['account_id'])
    op.create_index('ix_bank_txn_date', 'bank_transactions', ['date'])
    op.create_index('ix_bank_txn_type', 'bank_transactions', ['type'])
    op.create_index('ix_bank_txn_matched', 'bank_transactions', ['matched_crypto_transaction_id'])

    # Transaction Matches table
    op.create_table(
        'transaction_matches',
        sa.Column('id', sa.String(100), nullable=False),
        sa.Column('crypto_withdrawal_id', sa.String(100), nullable=False, index=True),
        sa.Column('bank_deposit_id', sa.String(100), nullable=False),
        sa.Column('crypto_amount', sa.Numeric(20, 8), nullable=False),
        sa.Column('crypto_currency', sa.String(20), nullable=False),
        sa.Column('fiat_amount', sa.Numeric(20, 8), nullable=False),
        sa.Column('fiat_currency', sa.String(10), nullable=False),
        sa.Column('exchange_rate', sa.Numeric(20, 8), nullable=False),
        sa.Column('fees_paid', sa.Numeric(20, 8), nullable=False),
        sa.Column('slippage', sa.Numeric(20, 8), nullable=False),
        sa.Column('crypto_date', sa.DateTime(), nullable=False),
        sa.Column('fiat_date', sa.DateTime(), nullable=False),
        sa.Column('time_delta_hours', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('match_status', sa.String(20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['bank_deposit_id'], ['bank_transactions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_match_crypto', 'transaction_matches', ['crypto_withdrawal_id'])
    op.create_index('ix_match_bank', 'transaction_matches', ['bank_deposit_id'])
    op.create_index('ix_match_confidence', 'transaction_matches', ['confidence'])

    # Price Events table
    op.create_table(
        'price_events',
        sa.Column('id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('event_type', sa.String(30), nullable=False),
        sa.Column('asset', sa.String(20), nullable=False, index=True),
        sa.Column('previous_price', sa.Numeric(20, 8), nullable=False),
        sa.Column('current_price', sa.Numeric(20, 8), nullable=False),
        sa.Column('price_change_pct', sa.Float(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_event_user', 'price_events', ['user_id'])
    op.create_index('ix_event_asset', 'price_events', ['asset'])
    op.create_index('ix_event_type', 'price_events', ['event_type'])

    # Tax Audit Trail table
    op.create_table(
        'tax_audit_trail',
        sa.Column('id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('transaction_id', sa.String(100), nullable=False),
        sa.Column('stage', sa.String(50), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('amount', sa.Numeric(20, 8), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False),
        sa.Column('proof_hash', sa.String(100), nullable=True),
        sa.Column('proof_metadata', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_user', 'tax_audit_trail', ['user_id'])
    op.create_index('ix_audit_timestamp', 'tax_audit_trail', ['timestamp'])

    # Crypto Withdrawals table
    op.create_table(
        'crypto_withdrawals',
        sa.Column('id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('exchange', sa.String(50), nullable=False),
        sa.Column('asset', sa.String(20), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(20, 8), nullable=False),
        sa.Column('amount_in_usd', sa.Numeric(20, 8), nullable=False),
        sa.Column('destination_address', sa.String(200), nullable=False),
        sa.Column('tx_hash', sa.String(200), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('matched_bank_deposit_id', sa.String(100), nullable=True),
        sa.Column('match_confidence', sa.Float(), nullable=False),
        sa.Column('date_time', sa.DateTime(), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_withdrawal_user', 'crypto_withdrawals', ['user_id'])
    op.create_index('ix_withdrawal_asset', 'crypto_withdrawals', ['asset'])
    op.create_index('ix_withdrawal_date', 'crypto_withdrawals', ['date_time'])


def downgrade() -> None:
    # Drop all tables in reverse order (respecting foreign key constraints)
    op.drop_index('ix_withdrawal_date', table_name='crypto_withdrawals')
    op.drop_index('ix_withdrawal_asset', table_name='crypto_withdrawals')
    op.drop_index('ix_withdrawal_user', table_name='crypto_withdrawals')
    op.drop_table('crypto_withdrawals')

    op.drop_index('ix_audit_timestamp', table_name='tax_audit_trail')
    op.drop_index('ix_audit_user', table_name='tax_audit_trail')
    op.drop_table('tax_audit_trail')

    op.drop_index('ix_event_type', table_name='price_events')
    op.drop_index('ix_event_asset', table_name='price_events')
    op.drop_index('ix_event_user', table_name='price_events')
    op.drop_table('price_events')

    op.drop_index('ix_match_confidence', table_name='transaction_matches')
    op.drop_index('ix_match_bank', table_name='transaction_matches')
    op.drop_index('ix_match_crypto', table_name='transaction_matches')
    op.drop_table('transaction_matches')

    op.drop_index('ix_bank_txn_matched', table_name='bank_transactions')
    op.drop_index('ix_bank_txn_type', table_name='bank_transactions')
    op.drop_index('ix_bank_txn_date', table_name='bank_transactions')
    op.drop_index('ix_bank_txn_account', table_name='bank_transactions')
    op.drop_table('bank_transactions')

    op.drop_index('ix_bank_status', table_name='bank_accounts')
    op.drop_index('ix_bank_user', table_name='bank_accounts')
    op.drop_table('bank_accounts')

    op.drop_index('ix_exec_timestamp', table_name='tlh_execution_history')
    op.drop_index('ix_exec_opportunity', table_name='tlh_execution_history')
    op.drop_table('tlh_execution_history')

    op.drop_index('ix_tlh_created', table_name='tlh_opportunities')
    op.drop_index('ix_tlh_status', table_name='tlh_opportunities')
    op.drop_index('ix_tlh_user_asset', table_name='tlh_opportunities')
    op.drop_table('tlh_opportunities')
