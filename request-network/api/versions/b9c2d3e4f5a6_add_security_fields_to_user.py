"""add security fields to user

Revision ID: b9c2d3e4f5a6
Revises: 5944b5decb15
Create Date: 2026-06-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b9c2d3e4f5a6'
down_revision = '5944b5decb15'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_login_ip', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('last_login_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('force_password_change', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('allowed_ips', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'))
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'allowed_ips')
    op.drop_column('users', 'force_password_change')
    op.drop_column('users', 'last_login_date')
    op.drop_column('users', 'last_login_ip')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
