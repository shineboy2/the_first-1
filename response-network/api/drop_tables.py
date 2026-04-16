import asyncio
from sqlalchemy import text
from db.session import async_session

async def drop_all():
    tables = [
        'incoming_requests',
        'query_results',
        'profile_type_request_access',
        'user_request_access',
        'request_type_parameters',
        'request_types',
        'user_settings',
        'settings',
        'requests',
        'users',
        'profile_type_configs',
        'worker_settings',
        'alembic_version'
    ]
    
    async with async_session() as session:
        for table in tables:
            try:
                await session.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
                print(f"Dropped table {table}")
            except Exception as e:
                print(f"Error dropping {table}: {str(e)}")
        await session.commit()
        print("Successfully dropped all tables.")

if __name__ == "__main__":
    asyncio.run(drop_all())