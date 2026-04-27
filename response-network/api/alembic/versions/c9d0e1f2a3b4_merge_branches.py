"""merge branches

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2, a1b2c3d4e5f6
Create Date: 2026-04-26 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, Sequence[str], None] = ('b7c8d9e0f1a2', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is a merge migration, no changes needed
    pass


def downgrade() -> None:
    # This is a merge migration, no changes needed
    pass
