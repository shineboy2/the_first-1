"""Add FTP profiles, file request configs, file requests tables and request_types execution_method

Revision ID: d4e5f6a7b8c9
Revises: 327bef145ceb
Create Date: 2026-06-05 17:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = '327bef145ceb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === FTP Profiles ===
    op.create_table(
        'ftp_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False, server_default='21'),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('password_encrypted', sa.Text(), nullable=True),
        sa.Column('base_path', sa.String(500), nullable=False, server_default='/'),
        sa.Column('use_tls', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('passive_mode', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('timeout', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_tested_at', sa.DateTime(), nullable=True),
        sa.Column('last_test_result', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ftp_profiles_name', 'ftp_profiles', ['name'], unique=True)
    op.create_index('ix_ftp_profiles_is_active', 'ftp_profiles', ['is_active'])

    # === File Request Configs ===
    op.create_table(
        'file_request_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        # FTP connections
        sa.Column('send_ftp_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('send_path', sa.String(500), nullable=False, server_default='/outgoing'),
        sa.Column('receive_ftp_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('receive_path', sa.String(500), nullable=False, server_default='/incoming'),
        # File generation
        sa.Column('filename_template', sa.String(500), nullable=False),
        sa.Column('content_format', sa.String(50), nullable=False, server_default='json'),
        sa.Column('content_template', postgresql.JSON(), nullable=True),
        sa.Column('content_encoding', sa.String(20), nullable=False, server_default='utf-8'),
        # Response parsing
        sa.Column('response_parser_config', postgresql.JSON(), nullable=True),
        sa.Column('response_timeout_minutes', sa.Integer(), nullable=False, server_default='1440'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('poll_interval_seconds', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('has_error_response', sa.Boolean(), nullable=False, server_default='false'),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['send_ftp_profile_id'], ['ftp_profiles.id']),
        sa.ForeignKeyConstraint(['receive_ftp_profile_id'], ['ftp_profiles.id']),
    )
    op.create_index('ix_file_request_configs_name', 'file_request_configs', ['name'], unique=True)

    # === File Requests (Tracker) ===
    op.create_table(
        'file_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incoming_request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_request_config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('filename', sa.String(500), nullable=True),
        sa.Column('file_content_hash', sa.String(64), nullable=True),
        # Timeline
        sa.Column('file_generated_at', sa.DateTime(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('response_detected_at', sa.DateTime(), nullable=True),
        sa.Column('response_downloaded_at', sa.DateTime(), nullable=True),
        sa.Column('parsed_at', sa.DateTime(), nullable=True),
        # Response data
        sa.Column('response_filename', sa.String(500), nullable=True),
        sa.Column('response_raw_content', sa.Text(), nullable=True),
        sa.Column('parsed_result', postgresql.JSON(), nullable=True),
        # Polling
        sa.Column('poll_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_poll_at', sa.DateTime(), nullable=True),
        # Error handling
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.String(1000), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['incoming_request_id'], ['incoming_requests.id']),
        sa.ForeignKeyConstraint(['file_request_config_id'], ['file_request_configs.id']),
    )
    op.create_index('ix_file_requests_status', 'file_requests', ['status'])
    op.create_index('ix_file_requests_incoming_request_id', 'file_requests', ['incoming_request_id'])

    # === Add execution_method to request_types ===
    op.add_column('request_types', sa.Column(
        'execution_method', sa.String(50), nullable=False, server_default='elasticsearch'
    ))
    op.add_column('request_types', sa.Column(
        'file_request_config_id', postgresql.UUID(as_uuid=True), nullable=True
    ))
    op.add_column('request_types', sa.Column(
        'external_api_id', postgresql.UUID(as_uuid=True), nullable=True
    ))
    op.create_foreign_key(
        'fk_request_types_file_request_config',
        'request_types', 'file_request_configs',
        ['file_request_config_id'], ['id']
    )
    op.create_foreign_key(
        'fk_request_types_external_api',
        'request_types', 'external_apis',
        ['external_api_id'], ['id']
    )


def downgrade() -> None:
    # Remove FK constraints from request_types
    op.drop_constraint('fk_request_types_external_api', 'request_types', type_='foreignkey')
    op.drop_constraint('fk_request_types_file_request_config', 'request_types', type_='foreignkey')
    op.drop_column('request_types', 'external_api_id')
    op.drop_column('request_types', 'file_request_config_id')
    op.drop_column('request_types', 'execution_method')

    # Drop tables in reverse order
    op.drop_table('file_requests')
    op.drop_table('file_request_configs')
    op.drop_table('ftp_profiles')
