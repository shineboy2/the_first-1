import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Env vars will be picked up from container
DB_USER = os.getenv("REQUEST_DB_USER", "user")
DB_PASS = os.getenv("REQUEST_DB_PASSWORD", "password")
DB_HOST = os.getenv("REQUEST_DB_HOST", "postgres-request-db")
DB_PORT = os.getenv("REQUEST_DB_PORT", "5432")
DB_NAME = os.getenv("REQUEST_DB_NAME", "request_db")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def reset_status():
    print(f"Connecting to DB...")
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("Resetting request status to 'pending'...")
        await conn.execute(text("UPDATE requests SET status = 'pending' WHERE status = 'exported'"))
        print("Done.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_status())
