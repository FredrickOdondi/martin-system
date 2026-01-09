"""add_pending_approval_to_minutesstatus

Revision ID: ece13bd7ad72
Revises: 398d9eb21944
Create Date: 2026-01-09 01:55:32.490545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ece13bd7ad72'
down_revision: Union[str, Sequence[str], None] = '398d9eb21944'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pending_approval to minutesstatus enum."""
    op.execute("ALTER TYPE minutesstatus ADD VALUE IF NOT EXISTS 'pending_approval'")


def downgrade() -> None:
    """Downgrade schema - cannot easily remove enum values in PostgreSQL."""
    # PostgreSQL doesn't support removing enum values directly
    # This would require creating a new enum type and migrating
    pass
