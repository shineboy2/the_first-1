"""add subuser rate limits

Revision ID: f6g7h8i9j0k1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6g7h8i9j0k1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('subuser_rate_limit_per_minute', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('users', sa.Column('subuser_rate_limit_per_hour', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('users', sa.Column('subuser_rate_limit_per_day', sa.Integer(), nullable=False, server_default='500'))


def downgrade() -> None:
    op.drop_column('users', 'subuser_rate_limit_per_day')
    op.drop_column('users', 'subuser_rate_limit_per_hour')
    op.drop_column('users', 'subuser_rate_limit_per_minute')
