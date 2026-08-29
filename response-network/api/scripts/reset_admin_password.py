import asyncio
import asyncpg
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def reset_password():
    conn = await asyncpg.connect(
        user="user",
        password="password",
        database="response_db",
        host="localhost",
        port=5433
    )
    
    try:
        new_password_hash = pwd_context.hash("admin123")
        
        result = await conn.execute(
            "UPDATE users SET hashed_password = $1 WHERE username = 'admin'",
            new_password_hash
        )
        
        print(f"Password reset for admin user: {result}")
        
        user = await conn.fetchrow(
            "SELECT username, email, is_active, profile_type FROM users WHERE username = 'admin'"
        )
        
        if user:
            print(f"\nAdmin user details:")
            print(f"  Username: {user['username']}")
            print(f"  Email: {user['email']}")
            print(f"  Is active: {user['is_active']}")
            print(f"  Profile type: {user['profile_type']}")
        else:
            print("\nAdmin user not found!")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(reset_password())
