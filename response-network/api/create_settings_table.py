import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

from models.settings import Settings, UserSettings
from core.config import settings
from shared.database.base import BaseModel

async def create_tables():
    # Construct DATABASE_URL from generic settings if DATABASE_URL property is not found
    # In Response Network, it might be slightly different
    db_user = os.getenv("RESPONSE_DB_USER", "postgres")
    db_pass = os.getenv("RESPONSE_DB_PASSWORD", "postgres")
    db_host = os.getenv("RESPONSE_DB_HOST", "postgres-response-db")
    db_port = os.getenv("RESPONSE_DB_PORT", "5432")
    db_name = os.getenv("RESPONSE_DB_NAME", "response_network")
    
    # Check if we should use asyncpg
    database_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    print(f"Connecting to {db_host}...")
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        # Create settings and user_settings tables
        await conn.run_sync(BaseModel.metadata.create_all, tables=[Settings.__table__, UserSettings.__table__])
    print("✓ Settings and UserSettings tables created successfully")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
