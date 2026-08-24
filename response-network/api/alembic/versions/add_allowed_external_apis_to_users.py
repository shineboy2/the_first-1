"""add allowed_external_apis to users

Revision ID: f1a2b3c4d5e6
Revises: c9d0e1f2a3b4
Create Date: 2026-04-27 14:43:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'c9d0e1f2a3b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add allowed_external_apis column to users table
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS allowed_external_apis JSONB DEFAULT '[]' NOT NULL")


def downgrade() -> None:
    # Remove allowed_external_apis column from users table
    op.drop_column('users', 'allowed_external_apis')
