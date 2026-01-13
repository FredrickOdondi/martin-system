"""ensure_minutes_enums

Revision ID: 8f452664dcf2
Revises: 72346a827bb1
Create Date: 2026-01-13 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f452664dcf2'
down_revision: Union[str, Sequence[str], None] = '72346a827bb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ensure Enum values exist."""
    # We use execute with IF NOT EXISTS to be safe (idempotent)
    # Note: 'pending_approval' might already exist from ece13bd7ad72, but ensuring it doesn't hurt if we chain correctly.
    # However, to avoid graph chaos, we just run the SQL commands.
    
    # 1. Add 'pending_approval' if missing (redundant safety)
    op.execute("ALTER TYPE minutesstatus ADD VALUE IF NOT EXISTS 'pending_approval'")
    
    # 2. Add 'review' (likely missing)
    op.execute("ALTER TYPE minutesstatus ADD VALUE IF NOT EXISTS 'review'")


def downgrade() -> None:
    pass
