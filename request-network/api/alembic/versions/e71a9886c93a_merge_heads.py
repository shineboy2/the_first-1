"""Merge heads

Revision ID: e71a9886c93a
Revises: 89b84af66906, b9c2d3e4f5a6
Create Date: 2026-06-08 09:22:21.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e71a9886c93a'
down_revision: Union[tuple[str, ...], str, None] = ('89b84af66906', 'b9c2d3e4f5a6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
