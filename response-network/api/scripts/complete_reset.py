import asyncio
from sqlalchemy import text
from db.session import async_session

async def complete_reset():
    async with async_session() as session:
        # Drop and recreate the public schema
        await session.execute(text('DROP SCHEMA public CASCADE'))
        await session.execute(text('CREATE SCHEMA public'))
        await session.execute(text('GRANT ALL ON SCHEMA public TO public'))
        await session.commit()
        print("Successfully reset the entire database schema.")

if __name__ == "__main__":
    asyncio.run(complete_reset())