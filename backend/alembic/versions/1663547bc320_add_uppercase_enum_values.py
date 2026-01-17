"""add_uppercase_enum_values

Revision ID: 1663547bc320
Revises: 3b4fefa89943
Create Date: 2026-01-16 22:40:58.265200

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1663547bc320'
down_revision: Union[str, Sequence[str], None] = '3b4fefa89943'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add UPPERCASE values to projectstatus enum because SQLAlchemy persists Names not Values
    op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'DRAFT'")
    op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'PIPELINE'")
    op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'UNDER_REVIEW'")
    op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'DECLINED'")
    op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'NEEDS_REVISION'")
    op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'SUMMIT_READY'")
    op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'DEAL_ROOM_FEATURED'")
    op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'IN_NEGOTIATION'")
    op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'COMMITTED'")
    op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'IMPLEMENTED'")
    op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'ON_HOLD'")
    op.execute("ALTER TYPE projectstatus ADD VALUE IF NOT EXISTS 'ARCHIVED'")


def downgrade() -> None:
    pass
