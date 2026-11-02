"""Add Latin American tax jurisdiction support

Revision ID: latam_tax_support_001
Revises: 2cb97027aaea
Create Date: 2026-04-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'latam_tax_support_001'
down_revision: Union[str, Sequence[str], None] = '2cb97027aaea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tax jurisdiction tables"""
    
    # Create tax_jurisdictions table
    op.create_table(
        'tax_jurisdictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=3), nullable=False, unique=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('region', sa.String(length=50), nullable=False),
        sa.Column('capital_gains_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('ordinary_income_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('vat_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('reporting_currency', sa.String(length=3), nullable=False),
        sa.Column('holding_period_days', sa.Integer(), nullable=False, server_default='365'),
        sa.Column('crypto_classification', sa.Text(), nullable=True),
        sa.Column('filing_frequency', sa.String(length=50), nullable=False),
        sa.Column('filing_authority', sa.String(length=100), nullable=False),
        sa.Column('filing_url', sa.Text(), nullable=True),
        sa.Column('tax_authority_api_url', sa.Text(), nullable=True),
        sa.Column('api_requires_auth', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_jurisdictions_code'), 'tax_jurisdictions', ['code'], unique=True)
    
    # Create tax_rules table
    op.create_table(
        'tax_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('jurisdiction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('tax_category', sa.String(length=50), nullable=False),
        sa.Column('calculation_method', sa.String(length=50), nullable=False),
        sa.Column('rate_tiers', sa.JSON(), nullable=True),
        sa.Column('holding_period_treatment', sa.String(length=50), nullable=True),
        sa.Column('holding_period_days', sa.Integer(), nullable=True),
        sa.Column('exclusion_threshold', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['jurisdiction_id'], ['tax_jurisdictions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_rules_jurisdiction_id'), 'tax_rules', ['jurisdiction_id'])
    
    # Create tax_form_templates table
    op.create_table(
        'tax_form_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('jurisdiction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('form_id', sa.String(length=50), nullable=False),
        sa.Column('form_name', sa.String(length=200), nullable=False),
        sa.Column('pdf_template_path', sa.String(length=255), nullable=True),
        sa.Column('xml_schema_path', sa.String(length=255), nullable=True),
        sa.Column('csv_export_fields', sa.JSON(), nullable=True),
        sa.Column('sections', sa.JSON(), nullable=True),
        sa.Column('required_fields', sa.JSON(), nullable=True),
        sa.Column('conditional_fields', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['jurisdiction_id'], ['tax_jurisdictions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_form_templates_jurisdiction_id'), 'tax_form_templates', ['jurisdiction_id'])
    
    # Create user_tax_profiles table
    op.create_table(
        'user_tax_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('jurisdiction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('tax_payer_name', sa.String(length=255), nullable=True),
        sa.Column('tax_address', sa.Text(), nullable=True),
        sa.Column('fiscal_year_start_month', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('fiscal_year_end_month', sa.Integer(), nullable=False, server_default='12'),
        sa.Column('calculation_method', sa.String(length=50), nullable=False, server_default='fifo'),
        sa.Column('preferred_tax_category', sa.String(length=50), nullable=True),
        sa.Column('preferred_export_formats', sa.String(length=255), nullable=False, server_default='PDF,CSV'),
        sa.Column('tax_advisor_email', sa.String(length=255), nullable=True),
        sa.Column('tax_advisor_name', sa.String(length=255), nullable=True),
        sa.Column('last_filed_year', sa.Integer(), nullable=True),
        sa.Column('last_filed_date', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['jurisdiction_id'], ['tax_jurisdictions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_tax_profiles_jurisdiction_id'), 'user_tax_profiles', ['jurisdiction_id'])
    op.create_index(op.f('ix_user_tax_profiles_user_id'), 'user_tax_profiles', ['user_id'])


def downgrade() -> None:
    """Drop tax jurisdiction tables"""
    
    op.drop_index(op.f('ix_user_tax_profiles_user_id'), table_name='user_tax_profiles')
    op.drop_index(op.f('ix_user_tax_profiles_jurisdiction_id'), table_name='user_tax_profiles')
    op.drop_table('user_tax_profiles')
    
    op.drop_index(op.f('ix_tax_form_templates_jurisdiction_id'), table_name='tax_form_templates')
    op.drop_table('tax_form_templates')
    
    op.drop_index(op.f('ix_tax_rules_jurisdiction_id'), table_name='tax_rules')
    op.drop_table('tax_rules')
    
    op.drop_index(op.f('ix_tax_jurisdictions_code'), table_name='tax_jurisdictions')
    op.drop_table('tax_jurisdictions')
