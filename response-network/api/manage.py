#!/usr/bin/env python3
"""
Management script for Response Network
Handles database initialization, seeding, and other admin tasks
"""
import asyncio
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db.session import async_engine, async_session_maker
from models.user import User
from models.profile_type import ProfileType
from core.hashing import get_password_hash
import uuid


async def seed_database():
    """Seed database with initial data"""
    async with async_session_maker() as session:
        # Check if admin already exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            print("✓ Admin user already exists, skipping seed")
            return

        print("🌱 Seeding database...")
        
        # Create profile types
        profile_types = [
            ProfileType(
                name="admin",
                display_name="Administrator",
                description="Full system access",
                is_active=True,
            ),
            ProfileType(
                name="user",
                display_name="Regular User",
                description="Standard user access",
                is_active=True,
            ),
        ]
        
        for pt in profile_types:
            session.add(pt)
        
        await session.flush()
        
        # Create admin user
        admin = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin@123456"),
            full_name="System Administrator",
            profile_type="admin",
            is_active=True,
        )
        
        session.add(admin)
        await session.commit()
        
        print("✓ Database seeded successfully")
        print(f"  - Admin user created: admin / admin@123456")


async def init_database():
    """Initialize database schema"""
    print("📦 Initializing database...")
    from .shared.database.base import Base
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✓ Database schema created")


async def main():
    """Run management commands"""
    if len(sys.argv) < 2:
        print("Usage: python manage.py <command>")
        print("Commands:")
        print("  seed   - Seed database with initial data")
        print("  init   - Initialize database schema")
        print("  migrate - Run Alembic migrations")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "seed":
        await seed_database()
    elif command == "init":
        await init_database()
    elif command == "migrate":
        import subprocess
        result = subprocess.run(["python", "-m", "alembic", "upgrade", "head"])
        sys.exit(result.returncode)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
