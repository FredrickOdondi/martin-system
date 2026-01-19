"""Add soft delete fields to projects table

Revision ID: 38a0e0f0d18c
Revises: 1663547bc320
Create Date: 2026-01-18 14:31:55.313168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38a0e0f0d18c'
down_revision: Union[str, Sequence[str], None] = '1663547bc320'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add soft delete fields
    op.add_column('projects', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('projects', sa.Column('deleted_by_id', sa.Uuid(), nullable=True))
    
    # Add timestamps
    op.add_column('projects', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('projects', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    
    # Add foreign key constraint for deleted_by_id
    op.create_foreign_key(
        'fk_projects_deleted_by_id_users',
        'projects', 'users',
        ['deleted_by_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraint
    op.drop_constraint('fk_projects_deleted_by_id_users', 'projects', type_='foreignkey')
    
    # Drop columns
    op.drop_column('projects', 'updated_at')
    op.drop_column('projects', 'created_at')
    op.drop_column('projects', 'deleted_by_id')
    op.drop_column('projects', 'deleted_at')
