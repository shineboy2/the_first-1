"""
Export settings to Request Network (Synchronous version)
"""
from datetime import datetime
import json
import os
import io
from pathlib import Path
import ftplib
import logging

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models.settings import Settings

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)

@shared_task
def export_settings_to_request_network():
    """Export all public settings to Request Network (Sync)."""
    
    # Build database URL from env
    db_user = os.getenv("RESPONSE_DB_USER", "postgres")
    db_pass = os.getenv("RESPONSE_DB_PASSWORD", "postgres")
    db_host = os.getenv("RESPONSE_DB_HOST", "127.0.0.1")
    db_port = os.getenv("RESPONSE_DB_PORT", "5432")
    db_name = os.getenv("RESPONSE_DB_NAME", "response_network")
    
    database_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    # Create sync engine and session
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get all public settings
        result = session.execute(
            select(Settings).where(Settings.is_public == True)
        )
        settings_list = result.scalars().all()
        
        # Retrieve dynamic export configuration
        config_result = session.execute(
            select(Settings).where(Settings.key == "settings_export_config")
        )
        config_setting = config_result.scalar_one_or_none()
        
        config = config_setting.value if config_setting else {}
        
        if not config.get("enabled", False):
             logger.info("Settings export is disabled.")
             return {"status": "skipped", "reason": "disabled"}
        
        # Prepare export data
        export_data = {
            "settings": [
                {
                    "id": str(setting.id),
                    "key": setting.key,
                    "value": setting.value,
                    "description": setting.description,
                    "is_public": setting.is_public,
                    "created_at": setting.created_at.isoformat() if setting.created_at else None,
                }
                for setting in settings_list
            ],
            "exported_at": datetime.utcnow().isoformat(),
            "total_count": len(settings_list),
        }
        
        filename = f"settings_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        storage_type = config.get("storage_type", "local")
        
        if storage_type == "local":
             local_path = Path(config.get("local_path", "/app/exports/settings"))
             if not local_path.exists():
                 local_path.mkdir(parents=True, exist_ok=True)
             
             file_path = local_path / filename
             with open(file_path, 'w', encoding='utf-8') as f:
                 json.dump(export_data, f, indent=2, ensure_ascii=False)
                 
             return {
                "status": "success",
                "exported_at": export_data["exported_at"],
                "total_count": len(settings_list),
                "file": str(file_path),
                "method": "local"
            }
            
        elif storage_type == "ftp":
            host = config.get("ftp_host")
            user = config.get("ftp_user")
            passwd = config.get("ftp_password")
            port = config.get("ftp_port", 21)
            # Use dedicated /settings path for settings export
            remote_path = "/settings"
            use_tls = config.get("ftp_use_tls", False)
            
            if not host:
                return {"status": "error", "reason": "ftp_host_missing"}
            
            try:
                # Prepare JSON data in memory
                json_data = json.dumps(export_data, indent=2, ensure_ascii=False).encode('utf-8')
                bio = io.BytesIO(json_data)
                
                # Connect to FTP server
                if use_tls:
                    ftp = ftplib.FTP_TLS()
                else:
                    ftp = ftplib.FTP()
                
                ftp.connect(host, port)
                ftp.login(user=user, passwd=passwd)
                
                # Try to change to remote path
                try:
                    ftp.cwd(remote_path)
                except ftplib.error_perm:
                    # Try to create
                    try:
                        ftp.mkd(remote_path)
                        ftp.cwd(remote_path)
                    except:
                        pass
                
                ftp.storbinary(f"STOR {filename}", bio)
                ftp.quit()
                
                return {
                    "status": "success",
                    "exported_at": export_data["exported_at"],
                    "total_count": len(settings_list),
                    "method": "ftp",
                    "destination": f"ftp://{host}{remote_path}/{filename}"
                }
            except Exception as e:
                logger.error(f"FTP Upload failed: {e}")
                return {"status": "error", "reason": f"ftp_failed: {str(e)}"}
        
        else:
             return {"status": "error", "reason": f"unknown_storage_type_{storage_type}"}

    except Exception as e:
        logger.error(f"Settings export failed: {e}")
        return {"status": "error", "reason": str(e)}
    finally:
        session.close()