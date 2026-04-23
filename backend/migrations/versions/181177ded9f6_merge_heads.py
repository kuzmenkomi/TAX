"""merge heads

Revision ID: 181177ded9f6
Revises: ce1b0b7f6f46, latam_tax_support_001
Create Date: 2026-04-22 14:41:03.198033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '181177ded9f6'
down_revision: Union[str, Sequence[str], None] = ('ce1b0b7f6f46', 'latam_tax_support_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
