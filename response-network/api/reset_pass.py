import asyncio
from db.session import get_db_session
from models.user import User
from core.hashing import get_password_hash
from sqlalchemy.future import select

async def main():
    async for session in get_db_session():
        result = await session.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        if user:
            user.hashed_password = get_password_hash("admin")
            await session.commit()
            print("Password reset to 'admin'")
        else:
            print("User admin not found")
        break

if __name__ == "__main__":
    asyncio.run(main())
