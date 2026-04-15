#!/usr/bin/env python3
"""
Bootstrap Import Configuration for Request Network
This script sets up the initial FTP import configuration WITHOUT requiring an admin user.
Run this ONCE after deploying the Request Network.

Usage:
    python3 bootstrap_import_config.py
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import sys
from pathlib import Path

# Add API directory to path
api_dir = Path(__file__).parent / "api"
sys.path.insert(0, str(api_dir))

from models.settings import Settings
from datetime import datetime


async def bootstrap_import_config():
    """Bootstrap import configuration for FTP."""
    
    # Build database URL
    db_user = os.getenv("REQUEST_DB_USER", "request_user")
    db_pass = os.getenv("REQUEST_DB_PASSWORD", "request_password")
    db_host = os.getenv("REQUEST_DB_HOST", "postgres")
    db_port = os.getenv("REQUEST_DB_PORT", "5432")
    db_name = os.getenv("REQUEST_DB_NAME", "request_db")
    
    db_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    print(f"🔗 Connecting to database: {db_host}:{db_port}/{db_name}")
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if import_config already exists
        result = await session.execute(
            select(Settings).where(Settings.key == "import_config")
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print("⚠️  Import config already exists. Skipping bootstrap.")
            print(f"   Current config: {existing.value}")
            return
        
        # Create import configuration
        import_config = Settings(
            key="import_config",
            value={
                "storage_type": "ftp",
                "enabled": True,
                "format": "json",
                "ftp_host": "192.168.214.139",
                "ftp_port": 21,
                "ftp_user": "request_ftp",
                "ftp_password": "ftp123",
                "ftp_path": "users",
                "ftp_use_tls": False
            },
            description="Import configuration for Request Network (bootstrapped)",
            is_public=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(import_config)
        await session.commit()
        
        print("✅ Import configuration bootstrapped successfully!")
        print(f"   FTP Host: 192.168.214.139:21")
        print(f"   FTP User: request_ftp")
        print(f"   FTP Path: /users/")
        print("\n📥 Now you can trigger the import to create the admin user from Response Network.")


if __name__ == "__main__":
    print("🚀 Bootstrapping Request Network Import Configuration...\n")
    asyncio.run(bootstrap_import_config())
