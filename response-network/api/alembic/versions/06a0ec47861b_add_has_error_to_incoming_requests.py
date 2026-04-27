"""add_has_error_to_incoming_requests

Revision ID: 06a0ec47861b
Revises: 10abcdef1234
Create Date: 2026-04-26 10:46:50.524309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06a0ec47861b'
down_revision: Union[str, None] = '10abcdef1234'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add has_error column as nullable first
    op.add_column('incoming_requests', sa.Column('has_error', sa.Boolean(), nullable=True))
    
    # Set default value for existing records
    op.execute("UPDATE incoming_requests SET has_error = FALSE WHERE has_error IS NULL")
    
    # Make the column NOT NULL
    op.alter_column('incoming_requests', 'has_error', nullable=False)
    
    # Add index
    op.create_index(op.f('ix_incoming_requests_has_error'), 'incoming_requests', ['has_error'], unique=False)


def downgrade() -> None:
    # Remove index
    op.drop_index(op.f('ix_incoming_requests_has_error'), table_name='incoming_requests')
    
    # Remove column
    op.drop_column('incoming_requests', 'has_error')