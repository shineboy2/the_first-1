"""Add has_error and error_message columns to responses table

Revision ID: b5c1d2e3f4a5
Revises: a0001_ensure_all_tables_exist
Create Date: 2026-04-25 13:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5c1d2e3f4a5'
down_revision = 'a0001_ensure_all_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add has_error and error_message columns to responses table"""
    # Add has_error column with default False and index
    op.add_column('responses', sa.Column('has_error', sa.Boolean(), server_default='false', nullable=False))
    op.create_index(op.f('ix_responses_has_error'), 'responses', ['has_error'], unique=False)
    
    # Add error_message column with 500 char limit
    op.add_column('responses', sa.Column('error_message', sa.String(500), nullable=True))


def downgrade() -> None:
    """Remove has_error and error_message columns from responses table"""
    op.drop_index(op.f('ix_responses_has_error'), table_name='responses')
    op.drop_column('responses', 'error_message')
    op.drop_column('responses', 'has_error')
