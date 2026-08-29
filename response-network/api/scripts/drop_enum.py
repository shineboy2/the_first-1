import asyncio
from sqlalchemy import text
from db.session import async_session

async def drop_enums():
    """Drop all enum types."""
    async with async_session() as session:
        # Drop enum types
        await session.execute(text("DROP TYPE IF EXISTS accesstype CASCADE"))
        await session.commit()
        print("Successfully dropped enum types.")

if __name__ == "__main__":
    asyncio.run(drop_enums())