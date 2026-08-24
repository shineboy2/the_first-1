"""add handler_class to external_apis

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-07-27 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'i9j0k1l2m3n4'
down_revision = 'h8i9j0k1l2m3'
branch_labels = None
depends_on = None

def upgrade():
    # Use raw SQL to add column if it does not exist
    op.execute(
        '''
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='external_apis' AND column_name='handler_class'
            ) THEN
                ALTER TABLE external_apis ADD COLUMN handler_class VARCHAR(100) NOT NULL DEFAULT 'generic';
            END IF;
        END $$;
        '''
    )

def downgrade():
    op.drop_column('external_apis', 'handler_class')
