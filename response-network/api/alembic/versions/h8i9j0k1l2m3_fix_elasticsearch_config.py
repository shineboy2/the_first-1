"""fix elasticsearch config

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-07-23 10:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'h8i9j0k1l2m3'
down_revision: Union[str, None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create elasticsearch_config if it doesn't exist. We use raw SQL to avoid errors if it DOES exist.
    op.execute("""
    CREATE TABLE IF NOT EXISTS elasticsearch_config (
        id UUID NOT NULL,
        url VARCHAR(255) NOT NULL,
        username VARCHAR(255),
        password VARCHAR(255),
        verify_ssl BOOLEAN DEFAULT true NOT NULL,
        is_active BOOLEAN DEFAULT true NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
        PRIMARY KEY (id)
    );
    """)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS elasticsearch_config;")
