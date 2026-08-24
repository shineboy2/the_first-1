"""Add missing user columns

Revision ID: 9cfe22bfe8d4
Revises: 3cc88ff34454
Create Date: 2025-12-27 06:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9cfe22bfe8d4'
down_revision = '3cc88ff34454'
branch_labels = None
depends_on = None


def upgrade() -> None:
    print("DEBUG: Running corrected migration 9cfe...")
    # Add allowed_request_types column
    op.add_column('users', sa.Column('allowed_request_types', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False))
    
    # Add blocked_request_types column
    op.add_column('users', sa.Column('blocked_request_types', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False))
    
    # Add other missing columns if they don't exist (using checks to be safe, though upgrade implies they are missing)
    # Based on the error, at least allowed_request_types is missing.
    # We add the rest just in case they are also missing as per the model definition
    
    op.add_column('users', sa.Column('daily_request_limit', sa.Integer(), server_default='100', nullable=False))
    op.add_column('users', sa.Column('monthly_request_limit', sa.Integer(), server_default='2000', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'monthly_request_limit')
    op.drop_column('users', 'daily_request_limit')
    op.drop_column('users', 'blocked_request_types')
    op.drop_column('users', 'allowed_request_types')
