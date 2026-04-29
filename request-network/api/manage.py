#!/usr/bin/env python3
"""
Management script for Request Network
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))


async def seed_database():
    """Request Network doesn't create users - they're imported from Response Network"""
    print("✓ Request Network uses user sync from Response Network")
    print("  Users will be automatically imported when Response Network exports them")


async def init_database():
    """Initialize database schema"""
    print("📦 Initializing Request Network database...")
    from .shared.database.base import Base
    import models  # Ensure all models are loaded
    from db.session import async_engine
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✓ Request Network database schema created")


async def main():
    """Run management commands"""
    if len(sys.argv) < 2:
        print("Usage: python manage.py <command>")
        print("Commands:")
        print("  init   - Initialize database schema")
        print("  migrate - Run Alembic migrations")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
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
