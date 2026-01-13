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
    
    Current state:
    - DRAFT, REVIEW, APPROVED, FINAL (uppercase - original)
    - pending_approval, review (lowercase - added later)
    
    Target state:
    - All UPPERCASE: DRAFT, REVIEW, APPROVED, FINAL, PENDING_APPROVAL
    
    PostgreSQL doesn't allow renaming enum values directly, so we need to:
    1. Add new uppercase values
    2. Update existing rows to use new values
    3. (Cannot remove old values without recreating enum, leave them as unused)
    """
    
    # 1. Add PENDING_APPROVAL (uppercase) if not exists
    op.execute("ALTER TYPE minutesstatus ADD VALUE IF NOT EXISTS 'PENDING_APPROVAL'")
    
    # 2. Update any rows using lowercase values to uppercase
    # Note: We commit after ADD VALUE, then update rows
    op.execute("UPDATE minutes SET status = 'DRAFT' WHERE status = 'draft'")
    op.execute("UPDATE minutes SET status = 'REVIEW' WHERE status = 'review'")
    op.execute("UPDATE minutes SET status = 'APPROVED' WHERE status = 'approved'")
    op.execute("UPDATE minutes SET status = 'FINAL' WHERE status = 'final'")
    op.execute("UPDATE minutes SET status = 'PENDING_APPROVAL' WHERE status = 'pending_approval'")


def downgrade() -> None:
    # Cannot easily remove enum values in PostgreSQL, leave as-is
    pass
