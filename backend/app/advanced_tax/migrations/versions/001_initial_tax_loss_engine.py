"""
Alembic migration for Tax-Loss Harvesting engine tables
Adds all necessary tables for TLH features
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'advanced_tax_engine_v1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create all tax-loss harvesting tables"""
    
    # Tax-Loss Harvesting opportunities
    op.create_table(
        'tax_loss_harvests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('country', sa.String(2), nullable=False, index=True),
        sa.Column('asset', sa.String(12), nullable=False, index=True),
        sa.Column('quantity', sa.DECIMAL(20, 8), nullable=False),
        sa.Column('quantity_to_sell', sa.DECIMAL(20, 8), nullable=False),
        sa.Column('purchase_price', sa.DECIMAL(20, 8), nullable=False),
        sa.Column('current_price', sa.DECIMAL(20, 8), nullable=False),
        sa.Column('cost_basis_method', sa.String(10), default='FIFO'),
        sa.Column('loss_amount', sa.DECIMAL(20, 2), nullable=False),
        sa.Column('loss_percentage', sa.Float(), nullable=False),
        sa.Column('estimated_fees', sa.DECIMAL(20, 2), default=0),
        sa.Column('fee_percentage', sa.Float(), default=0.1),
        sa.Column('tax_rate', sa.Float(), nullable=False),
        sa.Column('tax_savings', sa.DECIMAL(20, 2), nullable=False),
        sa.Column('wash_sale_days_remaining', sa.Integer(), default=0),
        sa.Column('last_sell_date', sa.DateTime(), nullable=True),
        sa.Column('volatility', sa.Float(), default=0),
        sa.Column('liquidity_score', sa.Float(), default=0),
        sa.Column('risk_level', sa.String(10), default='medium'),
        sa.Column('priority_score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(20), default='identified', index=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('executed_price', sa.DECIMAL(20, 8), nullable=True),
        sa.Column('exchange_id', sa.Integer(), nullable=True),
        sa.Column('rebuy_scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('rebuy_executed_at', sa.DateTime(), nullable=True),
        sa.Column('rebuy_price', sa.DECIMAL(20, 8), nullable=True),
        sa.Column('rebuy_asset', sa.String(12), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('audit_data', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Harvest actions (SELL, REBUY)
    op.create_table(
        'harvest_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('harvest_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(20), nullable=False),  # SELL, REBUY
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('quantity', sa.DECIMAL(20, 8), nullable=False),
        sa.Column('planned_price', sa.DECIMAL(20, 8), nullable=True),
        sa.Column('actual_price', sa.DECIMAL(20, 8), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('fee_paid', sa.DECIMAL(20, 8), default=0),
        sa.Column('transaction_hash', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['harvest_id'], ['tax_loss_harvests.id'], ondelete='CASCADE'),
    )
    
    # Missing cost basis (for reconciliation)
    op.create_table(
        'missing_cost_basis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('asset', sa.String(12), nullable=False),
        sa.Column('quantity', sa.DECIMAL(20, 8), nullable=False),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('error_description', sa.String(500), nullable=True),
        sa.Column('cost_basis', sa.DECIMAL(20, 8), nullable=True),
        sa.Column('cost_basis_source', sa.String(20), nullable=True),  # matched_send, manual, estimate
        sa.Column('matching_confidence', sa.Float(), default=0),
        sa.Column('potential_tax_impact', sa.DECIMAL(20, 2), nullable=True),
        sa.Column('severity_score', sa.Float(), default=0),
        sa.Column('resolved', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Reconciliation matches
    op.create_table(
        'reconciliation_matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('send_transaction_id', sa.Integer(), nullable=False),
        sa.Column('receive_transaction_id', sa.Integer(), nullable=False),
        sa.Column('matching_score', sa.Float(), nullable=False),  # 0-1 confidence
        sa.Column('matched_by', sa.String(20), nullable=False),  # user, system, ai
        sa.Column('matching_reason', sa.String(255), nullable=True),
        sa.Column('user_confirmed', sa.Boolean(), default=False),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Reconciliation history (audit trail)
    op.create_table(
        'reconciliation_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(20), nullable=False),  # UPDATE, DELETE, CREATE
        sa.Column('field_name', sa.String(50), nullable=True),
        sa.Column('old_value', sa.String(255), nullable=True),
        sa.Column('new_value', sa.String(255), nullable=True),
        sa.Column('changed_by', sa.String(50), nullable=True),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('reversible', sa.Boolean(), default=True),
        sa.Column('reversal_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Verified tax rules (accountant-verified)
    op.create_table(
        'verified_tax_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_code', sa.String(20), nullable=False, unique=True),
        sa.Column('rule_name', sa.String(200), nullable=False),
        sa.Column('country', sa.String(2), nullable=False, index=True),
        sa.Column('tax_type', sa.String(50), nullable=False),
        sa.Column('rule_definition', postgresql.JSON(), nullable=False),
        sa.Column('law_reference', sa.String(500), nullable=True),
        sa.Column('law_reference_url', sa.String(500), nullable=True),
        sa.Column('verified_by', sa.String(100), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=False),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('status', sa.String(20), default='active'),  # active, deprecated, under_review
        sa.Column('effective_from', sa.DateTime(), nullable=True),
        sa.Column('effective_until', sa.DateTime(), nullable=True),
        sa.Column('last_reviewed', sa.DateTime(), nullable=True),
        sa.Column('next_review', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Calculation audit records
    op.create_table(
        'calculation_audit_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('asset', sa.String(12), nullable=False),
        sa.Column('quantity', sa.DECIMAL(20, 8), nullable=False),
        sa.Column('buy_price', sa.DECIMAL(20, 8), nullable=False),
        sa.Column('sell_price', sa.DECIMAL(20, 8), nullable=False),
        sa.Column('tax_type', sa.String(50), nullable=False),
        sa.Column('tax_rate', sa.Float(), nullable=False),
        sa.Column('calculated_tax', sa.DECIMAL(20, 2), nullable=False),
        sa.Column('applied_rule_id', sa.Integer(), nullable=True),
        sa.Column('calculation_method', sa.String(50), nullable=False),
        sa.Column('reasoning', sa.String(500), nullable=True),
        sa.Column('verification_status', sa.String(20), default='unverified'),
        sa.Column('verified_by', sa.String(100), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('dispute_raised', sa.Boolean(), default=False),
        sa.Column('dispute_reason', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['applied_rule_id'], ['verified_tax_rules.id'], ondelete='SET NULL'),
    )
    
    # Audit packages (exports for tax authority)
    op.create_table(
        'audit_packages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('country', sa.String(2), nullable=False),
        sa.Column('tax_year', sa.Integer(), nullable=False),
        sa.Column('scope', sa.String(50), default='all'),  # all, exchanges, wallets, defi
        sa.Column('transaction_count', sa.Integer(), default=0),
        sa.Column('calculation_count', sa.Integer(), default=0),
        sa.Column('total_tax', sa.DECIMAL(20, 2), default=0),
        sa.Column('total_gains', sa.DECIMAL(20, 2), default=0),
        sa.Column('total_losses', sa.DECIMAL(20, 2), default=0),
        sa.Column('exported_json_path', sa.String(500), nullable=True),
        sa.Column('exported_pdf_path', sa.String(500), nullable=True),
        sa.Column('exported_excel_path', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), default='generating'),  # generating, ready, verified
        sa.Column('content_hash', sa.String(64), nullable=True),  # SHA256 for integrity
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('generated_by', sa.String(50), nullable=True),
        sa.Column('downloaded_at', sa.DateTime(), nullable=True),
        sa.Column('submitted_to_authority', sa.Boolean(), default=False),
        sa.Column('submission_date', sa.DateTime(), nullable=True),
        sa.Column('submission_reference', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for performance
    op.create_index('ix_tax_loss_harvests_user_country', 'tax_loss_harvests', 
                   ['user_id', 'country'])
    op.create_index('ix_tax_loss_harvests_status', 'tax_loss_harvests', ['status'])
    op.create_index('ix_missing_cost_basis_user', 'missing_cost_basis', 
                   ['user_id', 'resolved'])
    op.create_index('ix_calculation_audit_user_year', 'calculation_audit_records',
                   ['user_id', 'created_at'])
    op.create_index('ix_audit_packages_user_year', 'audit_packages',
                   ['user_id', 'tax_year'])


def downgrade():
    """Drop all tax-loss harvesting tables"""
    op.drop_table('audit_packages')
    op.drop_table('calculation_audit_records')
    op.drop_table('verified_tax_rules')
    op.drop_table('reconciliation_history')
    op.drop_table('reconciliation_matches')
    op.drop_table('missing_cost_basis')
    op.drop_table('harvest_actions')
    op.drop_table('tax_loss_harvests')
