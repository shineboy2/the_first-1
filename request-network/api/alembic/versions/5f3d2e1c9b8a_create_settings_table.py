"""create settings table

Revision ID: 5f3d2e1c9b8a
Revises: 9cfe22bfe8d4
Create Date: 2025-12-27 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5f3d2e1c9b8a'
down_revision = '9cfe22bfe8d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create settings table
    op.create_table('settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    
    # Create user_settings table
    op.create_table('user_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('user_settings')
    op.drop_table('settings')
