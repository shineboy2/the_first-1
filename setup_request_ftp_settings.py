import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Env vars will be picked up from container
DB_USER = os.getenv("REQUEST_DB_USER", "user")
DB_PASS = os.getenv("REQUEST_DB_PASSWORD", "password")
DB_HOST = os.getenv("REQUEST_DB_HOST", "postgres-request-db")
DB_PORT = os.getenv("REQUEST_DB_PORT", "5432")
DB_NAME = os.getenv("REQUEST_DB_NAME", "request_db")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# FTP Config
FTP_SETTINGS = {
    "export_destination_type": "ftp",
    "export_ftp_host": "192.168.214.139", # Host IP
    "export_ftp_port": "21",
    "export_ftp_username": "ftp_admin",
    "export_ftp_password": "123456", # Assuming standard dev password
    "export_ftp_path": "/request-data/exports", 
    "export_ftp_use_tls": "false"
}

async def setup_settings():
    print(f"Connecting to DB...")
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("Seeding FTP Settings...")
        
        # 1. Check if settings table exists
        # (It should, migration ran)
        
        for key, value in FTP_SETTINGS.items():
            # Check if exists
            res = await conn.execute(text(f"SELECT value FROM settings WHERE key = '{key}'"))
            row = res.fetchone()
            if row:
                print(f" -> Setting '{key}' exists: {row[0]}")
                # Update to ensure correctness
                if row[0] != value:
                    print(f"    Updating to '{value}'...")
                    await conn.execute(text(f"UPDATE settings SET value = '{value}', updated_at = now() WHERE key = '{key}'"))
            else:
                print(f" -> Setting '{key}' missing. Inserting '{value}'...")
                await conn.execute(text(f"""
                    INSERT INTO settings (key, value, description, is_public, created_at, updated_at)
                    VALUES ('{key}', '{value}', 'Injected by setup script', false, now(), now())
                """))
                
    print("Done.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup_settings())
