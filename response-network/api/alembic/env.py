import os
import sys

# Add the project root directories to sys.path
response_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if response_root not in sys.path:
    sys.path.insert(0, response_root)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Import all models here
from shared.database.base import Base
from shared.models.worker_settings import WorkerSettings
from models.user import User
from models.settings import Settings, UserSettings
from models.request_type import RequestType
from models.request_type_parameter import RequestTypeParameter
from models.request_access import UserRequestAccess
from models.profile_type_config import ProfileTypeConfig
from models.request import Request

# Load our config
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set SQLAlchemy metadata
target_metadata = Base.metadata


def get_database_url():
    """Build database URL from environment variables."""
    user = os.getenv("RESPONSE_DB_USER", os.getenv("DB_USER", "postgres"))
    password = os.getenv("RESPONSE_DB_PASSWORD", os.getenv("DB_PASSWORD", "postgres"))
    host = os.getenv("RESPONSE_DB_HOST", os.getenv("DB_HOST", "localhost"))
    port = os.getenv("RESPONSE_DB_PORT", os.getenv("DB_PORT", "5432"))
    db_name = os.getenv("RESPONSE_DB_NAME", os.getenv("DB_NAME", "response_network"))
    # Use psycopg (sync) for Alembic migrations
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"



def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Create engine directly from database URL
    connectable = engine_from_config(
        {"sqlalchemy.url": get_database_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
