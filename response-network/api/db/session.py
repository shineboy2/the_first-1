from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from core.config import settings

# Async engine for FastAPI
engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    echo=False,  # Set to True for debugging SQL queries
)

async_session = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Sync engine for Celery tasks
sync_database_url = str(settings.DATABASE_URL).replace(
    "postgresql+asyncpg://",
    "postgresql+psycopg://"
)
sync_engine = create_engine(
    sync_database_url,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI endpoints"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Aliases for compatibility
async_session_maker = async_session
async_engine = engine
