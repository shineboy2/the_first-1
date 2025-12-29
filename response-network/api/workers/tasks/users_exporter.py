"""
Users export task - Export users to request-network
"""
from datetime import datetime
import json
from pathlib import Path
import os
from dotenv import load_dotenv
import ftplib
import io

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Load .env file
load_dotenv()

# Import Settings model
from models.settings import Settings
import logging

logger = logging.getLogger(__name__)

# Import User model
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.user import User
# Import all models to resolve dependencies
from models.profile_type import ProfileType  # noqa
from models.request_type import RequestType  # noqa
from models.profile_type_request_access import ProfileTypeRequestAccess  # noqa
from models.profile_type_config import ProfileTypeConfig  # noqa


@shared_task
def export_users_to_request_network():
    """Export all active users to Request Network."""
    
    # Build database URL from env
    db_user = os.getenv("RESPONSE_DB_USER", "postgres")
    db_pass = os.getenv("RESPONSE_DB_PASSWORD", "postgres")
    db_host = os.getenv("RESPONSE_DB_HOST", "127.0.0.1")
    db_port = os.getenv("RESPONSE_DB_PORT", "5432")
    db_name = os.getenv("RESPONSE_DB_NAME", "response_network")
    
    database_url = f"postgresql+psycopg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
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
            logger.warning("Skipping user export: 'export_config' not set in settings.")
            return {"status": "skipped", "reason": "export_config_missing"}

        config = config_setting.value
        export_type = config.get("type", "local")
        
        # Determine Export Path
        if export_type == "local":
            export_path = Path(config.get("path", "/app/exports/users"))
        elif export_type == "ftp":
            # For phase 10, we will just simulate FTP by using a local temp path currently
            # Real implementation would use ftplib here based on creds
            export_path = Path("/tmp/ftp_exports/users") 
        else:
             logger.error(f"Unknown export type: {export_type}")
             return {"status": "error", "reason": f"unknown_type_{export_type}"}

        # Get all active users
        result = session.execute(
            select(User).where(User.is_active == True)
        )
        users = result.scalars().all()

        # Pre-fetch permissions mapping: Profile Name -> [Allowed Request Types]
        # Valid profiles only (orphans get nothing)
        perm_result = session.execute(
            select(ProfileTypeRequestAccess, RequestType)
            .join(RequestType, ProfileTypeRequestAccess.request_type_id == RequestType.id)
            .where(ProfileTypeRequestAccess.is_active == True)
        )
        
        # Build Map: {'agent': ['FlightBooking', 'HotelBooking'], 'admin': [...]}
        profile_permissions = {}
        for access, req_type in perm_result:
            if access.profile_type_id not in profile_permissions:
                profile_permissions[access.profile_type_id] = []
            profile_permissions[access.profile_type_id].append(req_type.name)
            
        # Add 'admin' implicit permissions for bootstrap (or if creating admin via script)
        # Though ideally this should be in DB, for now ensuring safety.
        # Check if 'admin' profile exists in configs
        admin_profile_check = session.execute(select(ProfileTypeConfig).where(ProfileTypeConfig.name == "admin")).scalar_one_or_none()
        if admin_profile_check:
             # Admin usually has access to everything, but let's respect the table.
             # If table is empty for admin, they get nothing unless we hardcode loophole OR ensure table is populated.
             # We assume table is populated correctly.
             pass
        
        # Prepare export data
        export_data = {
            "users": [
                {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "hashed_password": user.hashed_password,
                    "full_name": user.full_name if hasattr(user, 'full_name') else None,
                    "profile_type": user.profile_type or "user",
                    "is_active": user.is_active,
                    # Fields for Request Network with defaults
                    "profile_type": user.profile_type or "user",
                    "is_active": user.is_active,
                    # Fields for Request Network with defaults
                    "allowed_request_types": profile_permissions.get(user.profile_type, []),  # Sync actual permissions!
                    "blocked_request_types": [],  # Empty by default (can execute blocked logic if needed)
                    "rate_limit_per_minute": 200,  # Default rate limit
                    "rate_limit_per_hour": 1000,
                    "rate_limit_per_day": 5000,
                    "daily_request_limit": getattr(user, 'daily_request_limit', 1000),
                    "monthly_request_limit": getattr(user, 'monthly_request_limit', 10000),
                    "priority": 5,  # Default priority
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                }
                for user in users
            ],
            "exported_at": datetime.utcnow().isoformat(),
            "total_count": len(users),
        }
        
        # Save to latest.json
        latest_file = export_path / "latest.json"
        
        if export_type == "local":
            # Ensure export directory exists
            if not export_path.parent.exists():
                export_path.parent.mkdir(parents=True, exist_ok=True)
            if not export_path.exists():
                 export_path.mkdir(parents=True, exist_ok=True)
                 
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            # Update last export timestamp in DB
            # datetime is already imported at module level
            
            # Check if setting exists
            ts_result = session.execute(
                select(Settings).where(Settings.key == "last_user_export_at")
            )
            ts_setting = ts_result.scalar_one_or_none()
            
            if ts_setting:
                ts_setting.value = {"exported_at": export_data["exported_at"], "count": len(users)}
                ts_setting.updated_at = datetime.utcnow()
            else:
                ts_setting = Settings(
                    key="last_user_export_at",
                    value={"exported_at": export_data["exported_at"], "count": len(users)},
                    description="Last successful user export timestamp",
                    is_public=True
                )
                session.add(ts_setting)
            session.commit()

            return {
                "status": "success",
                "exported_at": export_data["exported_at"],
                "total_count": len(users),
                "file": str(latest_file),
                "config_used": export_type
            }
        
        elif export_type == "ftp":
            host = config.get("host")
            user = config.get("user")
            passwd = config.get("password")
            remote_path = config.get("path", "/users")
            
            if not host:
                return {"status": "error", "reason": "ftp_host_missing"}
            
            try:
                # Prepare JSON data in memory
                json_data = json.dumps(export_data, indent=2, ensure_ascii=False).encode('utf-8')
                bio = io.BytesIO(json_data)
                
                with ftplib.FTP(host) as ftp:
                    ftp.login(user=user, passwd=passwd)
                    # Try to change to remote path, create if not exist (simple version)
                    try:
                        ftp.cwd(remote_path)
                    except ftplib.error_perm:
                        # Try to create directories one by one or just assume they exist for now
                        # FTP doesn't have mkdir -p usually, so we'll just try to mkdir the last part
                        try:
                            ftp.mkd(remote_path)
                            ftp.cwd(remote_path)
                        except:
                            pass
                    
                    ftp.storbinary(f"STOR latest.json", bio)
                
                return {
                    "status": "success",
                    "exported_at": export_data["exported_at"],
                    "total_count": len(users),
                    "method": "ftp",
                    "destination": f"ftp://{host}{remote_path}/latest.json"
                }
            except Exception as e:
                logger.error(f"FTP Upload failed: {e}")
                return {"status": "error", "reason": f"ftp_failed: {str(e)}"}
    finally:
        session.close()


