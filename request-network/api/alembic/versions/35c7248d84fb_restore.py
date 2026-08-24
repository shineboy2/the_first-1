"""Restore

Revision ID: 35c7248d84fb
Revises: f4dec2ca4200
Create Date: 2026-08-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '35c7248d84fb'
down_revision = 'f4dec2ca4200'
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
