"""add field_mapping and index_mapping to request_types

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-08-23 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = 'j0k1l2m3n4o5'
down_revision = 'i9j0k1l2m3n4'
branch_labels = None
depends_on = None

def upgrade():
    # Add field_mapping column (JSON, nullable, default {})
    op.execute(
        '''
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='request_types' AND column_name='field_mapping'
            ) THEN
                ALTER TABLE request_types ADD COLUMN field_mapping JSON DEFAULT '{}';
            END IF;
        END $$;
        '''
    )
    # Add index_mapping column (JSON, nullable, default {})
    op.execute(
        '''
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='request_types' AND column_name='index_mapping'
            ) THEN
                ALTER TABLE request_types ADD COLUMN index_mapping JSON DEFAULT '{}';
            END IF;
        END $$;
        '''
    )

def downgrade():
    op.drop_column('request_types', 'index_mapping')
    op.drop_column('request_types', 'field_mapping')
