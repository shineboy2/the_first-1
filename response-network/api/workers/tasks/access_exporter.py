"""
Export user and profile type access to Request Network
"""
from datetime import datetime
import json
from pathlib import Path
import os
from dotenv import load_dotenv
import ftplib
import io
import logging

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Import models
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.user import User
from models.request_access import UserRequestAccess
from models.profile_type_request_access import ProfileTypeRequestAccess
from models.request_type import RequestType
from models.settings import Settings


@shared_task
def export_access_to_request_network():
    """
    Export user and profile type access to Request Network.
    
    DISABLED: Access control is now included in users_exporter.py.
    User permissions, blocked/allowed request types, and rate limits are exported
    as part of the user export data.
    """
    logger.info("Access export is disabled - permissions are included in users_exporter.py")
    return {
        "status": "disabled",
        "reason": "Access export has been consolidated into users_exporter.py to avoid redundancy"
    }
    
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
        # Fetch Export Configuration
        result = session.execute(
            select(Settings).where(Settings.key == "export_config")
        )
        config_setting = result.scalar_one_or_none()
        
        if not config_setting or not config_setting.value:
            logger.warning("Skipping access export: 'export_config' not set in settings.")
            return {"status": "skipped", "reason": "export_config_missing"}

        config = config_setting.value
        if not config.get("enabled", False):
            logger.info("Access export is disabled in configuration.")
            return {"status": "skipped", "reason": "disabled"}

        export_type = config.get("storage_type", "local")
        logger.info(f"Export type determined as: {export_type}")

        # Get all user request access
        user_access_result = session.execute(
            select(UserRequestAccess)
            .join(User, UserRequestAccess.user_id == User.id)
            .where(User.is_active == True)
        )
        user_access_list = user_access_result.scalars().all()
        logger.info(f"Found {len(user_access_list)} user access records.")

        # Get all profile type request access
        profile_access_result = session.execute(
            select(ProfileTypeRequestAccess)
            .where(ProfileTypeRequestAccess.is_active == True)
        )
        profile_access_list = profile_access_result.scalars().all()
        logger.info(f"Found {len(profile_access_list)} profile type access records.")

        # Get request type names for reference
        request_types_result = session.execute(select(RequestType))
        request_types_map = {str(rt.id): rt.name for rt in request_types_result.scalars().all()}

        # Prepare export data
        export_data = {
            "user_access": [
                {
                    "user_id": str(access.user_id),
                    "request_type_id": str(access.request_type_id),
                    "request_type_name": request_types_map.get(str(access.request_type_id), "unknown"),
                    "max_requests_per_hour": access.max_requests_per_hour,
                    "is_active": access.is_active,
                    "created_at": access.created_at.isoformat() if access.created_at else None,
                    "updated_at": access.updated_at.isoformat() if access.updated_at else None
                }
                for access in user_access_list
            ],
            "profile_type_access": [
                {
                    "profile_type_id": access.profile_type_id,
                    "request_type_id": str(access.request_type_id),
                    "request_type_name": request_types_map.get(str(access.request_type_id), "unknown"),
                    "max_requests_per_day": access.max_requests_per_day,
                    "max_requests_per_month": access.max_requests_per_month,
                    "is_active": access.is_active,
                    "created_at": access.created_at.isoformat() if access.created_at else None,
                    "updated_at": access.updated_at.isoformat() if access.updated_at else None
                }
                for access in profile_access_list
            ],
            "exported_at": datetime.utcnow().isoformat(),
            "user_access_count": len(user_access_list),
            "profile_access_count": len(profile_access_list),
        }
        
        filename = "latest.json"
        
        if export_type == "local":
            export_path = Path(config.get("local_path", "/app/exports/access"))
            if not export_path.exists():
                export_path.mkdir(parents=True, exist_ok=True)
            
            latest_file = export_path / filename
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported access locally to {latest_file}")
            return {
                "status": "success",
                "exported_at": export_data["exported_at"],
                "user_access_count": len(user_access_list),
                "profile_access_count": len(profile_access_list),
                "method": "local",
                "file": str(latest_file)
            }
            
        elif export_type == "ftp":
            host = config.get("ftp_host")
            user = config.get("ftp_user")
            passwd = config.get("ftp_password")
            port = config.get("ftp_port") or 21
            remote_path = "/access"  # Fixed path for access exports
            use_tls = config.get("ftp_use_tls", False)
            
            logger.info(f"Connecting to FTP: {host}:{port}")
            
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
                    try:
                        ftp.mkd(remote_path)
                        ftp.cwd(remote_path)
                    except Exception as e:
                        logger.warning(f"Could not create/change to {remote_path}: {e}")
                
                ftp.storbinary(f"STOR {filename}", bio)
                ftp.quit()
                
                logger.info(f"Exported access to FTP: {host}{remote_path}/{filename}")
                return {
                    "status": "success",
                    "exported_at": export_data["exported_at"],
                    "user_access_count": len(user_access_list),
                    "profile_access_count": len(profile_access_list),
                    "method": "ftp",
                    "destination": f"ftp://{host}{remote_path}/{filename}"
                }
            except Exception as e:
                logger.error(f"FTP Upload failed: {e}")
                return {"status": "error", "reason": f"ftp_failed: {str(e)}"}
        
        else:
            return {"status": "error", "reason": f"unknown_export_type: {export_type}"}
    
    except Exception as e:
        logger.error(f"Access export failed: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}
    finally:
        session.close()
