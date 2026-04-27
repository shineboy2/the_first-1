"""create_external_apis_table

Revision ID: b7c8d9e0f1a2
Revises: 06a0ec47861b
Create Date: 2026-04-26 13:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = '06a0ec47861b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('external_apis',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('endpoint_url', sa.String(length=500), nullable=False),
        sa.Column('http_method', sa.String(length=20), nullable=False, server_default='POST'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auth_type', sa.String(length=50), nullable=False, server_default='none'),
        sa.Column('auth_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('static_headers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('payload_template', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_external_apis_name'), 'external_apis', ['name'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_external_apis_name'), table_name='external_apis')
    op.drop_table('external_apis')
