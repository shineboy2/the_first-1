"""add_user_limits_response

Revision ID: 10abcdef1234
Revises: 06eb34f02521
Create Date: 2025-12-31 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '10abcdef1234'
down_revision = '06eb34f02521'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('users', sa.Column('rate_limit_per_minute', sa.Integer(), server_default='10', nullable=False))
    op.add_column('users', sa.Column('rate_limit_per_hour', sa.Integer(), server_default='100', nullable=False))
    op.add_column('users', sa.Column('rate_limit_per_day', sa.Integer(), server_default='500', nullable=False))
    
    op.add_column('users', sa.Column('priority', sa.Integer(), server_default='5', nullable=False))
    
    op.add_column('users', sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True))
    
    op.add_column('users', sa.Column('allowed_request_types', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False))
    op.add_column('users', sa.Column('blocked_request_types', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False))

def downgrade() -> None:
    op.drop_column('users', 'blocked_request_types')
    op.drop_column('users', 'allowed_request_types')
    op.drop_column('users', 'synced_at')
    op.drop_column('users', 'priority')
    op.drop_column('users', 'rate_limit_per_day')
    op.drop_column('users', 'rate_limit_per_hour')
    op.drop_column('users', 'rate_limit_per_minute')
