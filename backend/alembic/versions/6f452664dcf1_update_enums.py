"""update_enums

Revision ID: 6f452664dcf1
Revises: e637b1a43493
Create Date: 2026-01-11 13:40:19.310636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f452664dcf1'
down_revision: Union[str, Sequence[str], None] = 'e637b1a43493'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    """Upgrade schema."""
    # Postgres specific enum updates
    op.execute("ALTER TYPE meetingstatus ADD VALUE IF NOT EXISTS 'REQUESTED'")
    op.execute("ALTER TYPE conflicttype ADD VALUE IF NOT EXISTS 'VIP_AVAILABILITY'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
