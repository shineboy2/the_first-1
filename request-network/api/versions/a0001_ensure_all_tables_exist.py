"""Ensure all required tables exist - comprehensive migration

Revision ID: a0001_ensure_all_tables
Revises: 5944b5decb15
Create Date: 2026-04-18 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'a0001_ensure_all_tables'
down_revision = '5944b5decb15'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check and create settings table if it doesn't exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'settings' not in inspector.get_table_names():
        op.create_table('settings',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
            sa.Column('key', sa.String(length=100), nullable=False, unique=True),
            sa.Column('value', sa.JSON(), nullable=False),
            sa.Column('description', sa.String(length=500), nullable=True),
            sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('key'),
            schema='public'
        )
        # Create index for settings
        op.create_index('idx_settings_key', 'settings', ['key'], unique=True, schema='public')
    
    # Check and create user_settings table if it doesn't exist
    if 'user_settings' not in inspector.get_table_names():
        op.create_table('user_settings',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
            sa.Column('user_id', sa.String(length=36), nullable=False),
            sa.Column('key', sa.String(length=100), nullable=False),
            sa.Column('value', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            schema='public'
        )
        # Create index for user_settings
        op.create_index('idx_user_settings_user_id', 'user_settings', ['user_id'], schema='public')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'user_settings' in inspector.get_table_names():
        op.drop_table('user_settings', schema='public')
    
    if 'settings' in inspector.get_table_names():
        op.drop_table('settings', schema='public')
