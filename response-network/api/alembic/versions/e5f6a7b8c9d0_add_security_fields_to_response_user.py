"""add security fields to response network user

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-06 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('users', sa.Column('force_password_change', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('allowed_ips', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'))
    op.add_column('users', sa.Column('password_changed_at', sa.TIMESTAMP(timezone=True), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'allowed_ips')
    op.drop_column('users', 'force_password_change')
