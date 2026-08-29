import asyncio
from sqlalchemy import text
from db.session import async_session

async def reset_migrations():
    async with async_session() as session:
        # Drop all tables
        await session.execute(text('DROP TABLE IF EXISTS alembic_version CASCADE'))
        await session.execute(text('DROP TABLE IF EXISTS settings CASCADE'))
        await session.execute(text('DROP TABLE IF EXISTS user_settings CASCADE'))
        await session.execute(text('DROP TABLE IF EXISTS user_request_access CASCADE'))
        await session.execute(text('DROP TABLE IF EXISTS request_types CASCADE'))
        await session.execute(text('DROP TABLE IF EXISTS users CASCADE'))
        await session.commit()
        print("Successfully reset database and removed all migration history.")

if __name__ == "__main__":
    asyncio.run(reset_migrations())