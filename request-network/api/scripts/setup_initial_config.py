import asyncio
import sys
import os
import argparse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add api directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from models.settings import Settings
from core.config import settings

async def setup_config(ftp_host, ftp_user, ftp_pass, ftp_path):
    print("🔧 Setting up Initial FTP Configuration...")
    
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    config_value = {
        "type": "ftp",
        "host": ftp_host,
        "user": ftp_user,
        "password": ftp_pass,
        "path": ftp_path
    }
    
    async with async_session() as session:
        # 1. Update/Insert IMPORT Config
        result = await session.execute(select(Settings).where(Settings.key == "import_config"))
        import_setting = result.scalar_one_or_none()
        
        if import_setting:
            import_setting.value = config_value
            print("  ✓ Updated existing 'import_config'")
        else:
            session.add(Settings(key="import_config", value=config_value, description="Initial Import Config", is_public=False))
            print("  ✓ Created new 'import_config'")
            
        # 2. Update/Insert EXPORT Config
        result = await session.execute(select(Settings).where(Settings.key == "export_config"))
        export_setting = result.scalar_one_or_none()
        
        if export_setting:
            export_setting.value = config_value
            print("  ✓ Updated existing 'export_config'")
        else:
            session.add(Settings(key="export_config", value=config_value, description="Initial Export Config", is_public=False))
            print("  ✓ Created new 'export_config'")
        
        await session.commit()
    
    print("✅ Configuration applied successfully!")
    print("👉 Now restart the 'users-importer' worker to sync users.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Initial FTP Configuration")
    parser.add_argument("--host", required=True, help="FTP Host IP")
    parser.add_argument("--user", required=True, help="FTP Username")
    parser.add_argument("--password", required=True, help="FTP Password")
    parser.add_argument("--path", default="/upload", help="FTP Upload Path")
    
    args = parser.parse_args()
    
    asyncio.run(setup_config(args.host, args.user, args.password, args.path))
