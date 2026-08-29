import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db_session
from crud import users as user_service

async def test_auth():
    try:
        async for db in get_db_session():
            user = await user_service.authenticate(
                db, 
                username="admin",
                password="admin"
            )
            if user:
                print(f"Authentication successful! User: {user.username}")
                print(f"User details: {user.email}, {user.profile_type}")
            else:
                print("Authentication failed!")
    except Exception as e:
        print(f"Error during authentication: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_auth())