import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import settings
from models.user import User
from sqlalchemy.future import select

async def check_users():
    # Create async engine
    engine = create_async_engine(str(settings.DATABASE_URL))
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print("\nAll Users in Database:")
        print("-----------------------")
        for user in users:
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Hashed Password: {user.hashed_password}")
            print(f"Profile Type: {user.profile_type}")
            print(f"Is Active: {user.is_active}")
            print("-----------------------")

if __name__ == "__main__":
    asyncio.run(check_users())