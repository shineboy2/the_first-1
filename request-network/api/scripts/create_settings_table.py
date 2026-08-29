import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from models.settings import Settings, UserSettings
from core.config import settings
from shared.database.base import BaseModel

async def create_tables():
    engine = create_async_engine(str(settings.DATABASE_URL))
    async with engine.begin() as conn:
        # Create settings and user_settings tables
        await conn.run_sync(BaseModel.metadata.create_all, tables=[Settings.__table__, UserSettings.__table__])
    print("✓ Settings and UserSettings tables created")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
