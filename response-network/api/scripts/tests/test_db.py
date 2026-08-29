import asyncio
import asyncpg

async def test_connection():
    dsn = 'postgresql://user:password@localhost:5433/response_db'
    conn = await asyncpg.connect(dsn=dsn
    )
    try:
        result = await conn.fetch('SELECT 1')
        print("Connected successfully!")
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_connection())