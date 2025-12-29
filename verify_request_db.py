import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Env vars are loaded automatically inside container usually
DB_USER = os.getenv("REQUEST_DB_USER", "user")
DB_PASS = os.getenv("REQUEST_DB_PASSWORD", "password")
DB_HOST = os.getenv("REQUEST_DB_HOST", "postgres-request-db")
DB_PORT = os.getenv("REQUEST_DB_PORT", "5432")
DB_NAME = os.getenv("REQUEST_DB_NAME", "request_db")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def check_requests():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)

    async with engine.begin() as conn:
        print("Checking 'requests' table...")
        result = await conn.execute(text("SELECT id, status, query_type, created_at FROM requests"))
        rows = result.fetchall()
        
        if not rows:
            print("!!! NO REQUESTS FOUND IN DB !!!")
        else:
            print(f"Found {len(rows)} requests:")
            for row in rows:
                print(f" - ID: {row[0]} | Status: {row[1]} | Type: {row[2]} | Created: {row[3]}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_requests())
