"""add object_storage_configs table and request_types columns

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-08-24 06:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, TEXT

# revision identifiers, used by Alembic.
revision = 'k1l2m3n4o5p6'
down_revision = 'j0k1l2m3n4o5'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create object_storage_configs table
    op.execute('''
        CREATE TABLE IF NOT EXISTS object_storage_configs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL UNIQUE,
            display_name VARCHAR(200) NOT NULL,
            description VARCHAR(500),
            storage_type VARCHAR(20) NOT NULL DEFAULT 'minio',
            endpoint_url VARCHAR(500) NOT NULL,
            access_key VARCHAR(255) NOT NULL,
            secret_key_encrypted TEXT NOT NULL,
            region VARCHAR(50) NOT NULL DEFAULT 'us-east-1',
            default_bucket VARCHAR(255) NOT NULL,
            use_ssl BOOLEAN NOT NULL DEFAULT FALSE,
            verify_ssl BOOLEAN NOT NULL DEFAULT FALSE,
            path_style BOOLEAN NOT NULL DEFAULT TRUE,
            timeout INTEGER NOT NULL DEFAULT 30,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            last_tested_at TIMESTAMPTZ,
            last_test_result VARCHAR(500),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    ''')

    # Create index on name and is_active
    op.execute('''
        CREATE INDEX IF NOT EXISTS ix_object_storage_configs_name
            ON object_storage_configs (name);
    ''')
    op.execute('''
        CREATE INDEX IF NOT EXISTS ix_object_storage_configs_is_active
            ON object_storage_configs (is_active);
    ''')

    # 2. Add object_storage_config_id FK column to request_types
    op.execute('''
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='request_types' AND column_name='object_storage_config_id'
            ) THEN
                ALTER TABLE request_types
                    ADD COLUMN object_storage_config_id UUID
                    REFERENCES object_storage_configs(id);
            END IF;
        END $$;
    ''')

    # 3. Add object_storage_mapping JSON column to request_types
    op.execute('''
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='request_types' AND column_name='object_storage_mapping'
            ) THEN
                ALTER TABLE request_types
                    ADD COLUMN object_storage_mapping JSON;
            END IF;
        END $$;
    ''')


def downgrade():
    # Remove columns from request_types
    op.execute('''
        ALTER TABLE request_types
            DROP COLUMN IF EXISTS object_storage_mapping;
    ''')
    op.execute('''
        ALTER TABLE request_types
            DROP COLUMN IF EXISTS object_storage_config_id;
    ''')

    # Drop table
    op.execute('DROP TABLE IF EXISTS object_storage_configs CASCADE;')
