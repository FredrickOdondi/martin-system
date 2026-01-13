"""standardize_minutesstatus_enum_to_uppercase

Revision ID: 9a452664dcf3
Revises: 8f452664dcf2
Create Date: 2026-01-14 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a452664dcf3'
down_revision: Union[str, Sequence[str], None] = '8f452664dcf2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Standardize minutesstatus enum to all UPPERCASE values.
    
    Current DB state (from direct query):
    - DRAFT, REVIEW, APPROVED, FINAL (uppercase - original values)
    - pending_approval, review (lowercase - added by previous migration)
    
    Target state:
    - All UPPERCASE: DRAFT, REVIEW, APPROVED, FINAL, PENDING_APPROVAL
    
    Strategy:
    1. Add PENDING_APPROVAL (uppercase) if not exists
    2. Update rows using lowercase 'pending_approval' to uppercase 'PENDING_APPROVAL'
       Using text cast for WHERE clause since 'pending_approval' IS a valid enum value
    """
    
    # 1. Add PENDING_APPROVAL (uppercase) if not exists
    op.execute("ALTER TYPE minutesstatus ADD VALUE IF NOT EXISTS 'PENDING_APPROVAL'")
    
    # 2. Update rows that use the lowercase 'pending_approval' (which IS a valid enum value)
    # The lowercase 'pending_approval' exists in the DB, so we can query it directly
    op.execute("UPDATE minutes SET status = 'PENDING_APPROVAL' WHERE status = 'pending_approval'")
    
    # Note: We do NOT update DRAFT, REVIEW, APPROVED, FINAL because:
    # - The DB only has uppercase versions of these
    # - There are no lowercase 'draft', 'review', etc. in the DB to convert


def downgrade() -> None:
    # Cannot easily remove enum values in PostgreSQL, leave as-is
    pass
