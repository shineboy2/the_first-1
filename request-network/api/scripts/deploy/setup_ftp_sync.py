import asyncio
import sys
import os
import argparse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add api directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import Settings model
# We might need to adjust imports depending on where this is run
try:
    from models.settings import Settings
    from core.config import settings
except ImportError:
    # If run in a context where core/models are not in path
    sys.path.append("/app")
    from models.settings import Settings
    from core.config import settings

async def setup_config(ftp_host, ftp_user, ftp_pass, ftp_path):
    print(f"🔧 Setting up FTP Sync for {ftp_host}...")
    
    # We use settings.DATABASE_URL from core.config
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Base config values per ImportStorageService requirements
    config_value = {
        "storage_type": "ftp",
        "ftp_host": ftp_host,
        "ftp_user": ftp_user,
        "ftp_password": ftp_pass,
        "ftp_port": 21,
        "ftp_use_tls": False
    }
    
    # If ftp_path is provided, add it to the config
    # If NOT provided, ImportStorageService will default to /{resource_type}
    if ftp_path:
        config_value["ftp_path"] = ftp_path
    
    keys_to_update = [
        "import_config",
        "user_import_config",
        "settings_import_config",
        "export_config"
    ]
    
    async with async_session() as session:
        for key in keys_to_update:
            result = await session.execute(select(Settings).where(Settings.key == key))
            setting = result.scalar_one_or_none()
            
            if setting:
                setting.value = config_value
                print(f"  ✓ Updated existing '{key}'")
            else:
                session.add(Settings(
                    key=key, 
                    value=config_value, 
                    description=f"FTP Sync Config for {key}", 
                    is_public=False
                ))
                print(f"  ✓ Created new '{key}'")
        
        await session.commit()
    
    print("✅ Configuration applied successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup FTP Sync Configuration")
    parser.add_argument("--host", required=True, help="FTP Host IP")
    parser.add_argument("--user", required=True, help="FTP Username")
    parser.add_argument("--password", required=True, help="FTP Password")
    parser.add_argument("--path", default=None, help="FTP Base Path (optional)")
    
    args = parser.parse_args()
    
    asyncio.run(setup_config(args.host, args.user, args.password, args.path))
