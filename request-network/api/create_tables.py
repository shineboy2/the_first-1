import asyncio
import sys
from pathlib import Path

# Add core paths
api_dir = Path(__file__).resolve().parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from .shared.database.base import Base
from db.session import async_engine
import models  # Import all models to register them with Base

async def init_db():
    print("🚀 Explicitly initializing database schema...")
    async with async_engine.begin() as conn:
        # Import models inside to ensure they are available
        from models.user import User
        from models.request import Request
        from models.response import Response
        from models.api_key import ApiKey
        from models.settings import Settings
        
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Schema created successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
