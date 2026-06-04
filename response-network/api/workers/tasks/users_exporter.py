"""
Users export task - Export users to request-network (Improved)
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

# Import Settings model
from models.settings import Settings
from models.sync_history import SyncHistory

logger = logging.getLogger(__name__)

# Import User model
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.user import User

# Import all models to resolve dependencies
from models.profile_type import ProfileType  # noqa
from models.request_type import RequestType  # noqa
from models.request_access import UserRequestAccess  # noqa
from models.profile_type_request_access import ProfileTypeRequestAccess  # noqa
from models.profile_type_config import ProfileTypeConfig  # noqa


@shared_task
def export_users_to_request_network():
    """Export all active users to Request Network."""
    logger.info("Starting user export task...")
    
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
        # Create SyncHistory record
        sync_history = SyncHistory(
            operation_type="user_export",
            status="in_progress"
        )
        session.add(sync_history)
        session.commit()
        session.refresh(sync_history)

        # Fetch Export Configuration
        result = session.execute(
            select(Settings).where(Settings.key == "export_config")
        )
        config_setting = result.scalar_one_or_none()
        
        if not config_setting or not config_setting.value:
            logger.warning("Skipping user export: 'export_config' not set in settings.")
            return {"status": "skipped", "reason": "export_config_missing"}

        config = config_setting.value
        if not config.get("enabled", False):
             logger.info("User export is disabled in configuration.")
             sync_history.status = "skipped"
             sync_history.details = {"reason": "disabled"}
             sync_history.completed_at = datetime.utcnow()
             session.commit()
             return {"status": "skipped", "reason": "disabled"}

        export_type = config.get("storage_type", "local")
        logger.info(f"Export type determined as: {export_type}")

        # Get all active users
        result = session.execute(
            select(User).where(User.is_active == True)
        )
        users = result.scalars().all()
        logger.info(f"Found {len(users)} active users to export.")

        # Pre-fetch profile type configs with permissions
        profile_result = session.execute(
            select(ProfileTypeConfig)
        )
        profile_configs = {pt.name: pt for pt in profile_result.scalars().all()}
        logger.info(f"Pre-fetched {len(profile_configs)} profile type configurations.")
        
        # Pre-fetch request types (for converting IDs to names)
        request_types_result = session.execute(
            select(RequestType)
        )
        request_types_by_id = {rt.id: rt.name for rt in request_types_result.scalars().all()}
        logger.info(f"Pre-fetched {len(request_types_by_id)} request types.")
        
        # Pre-fetch user-specific access records
        user_access_result = session.execute(
            select(UserRequestAccess)
        )
        user_access_records = user_access_result.scalars().all()
        # Group by user_id for easy lookup
        user_access_by_user_id = {}
        for access in user_access_records:
            if access.user_id not in user_access_by_user_id:
                user_access_by_user_id[access.user_id] = []
            user_access_by_user_id[access.user_id].append(access)
        logger.info(f"Pre-fetched {len(user_access_records)} user-specific access records for {len(user_access_by_user_id)} users.")
        
        # Helper function to merge profile type and user-specific permissions
        def merge_user_permissions(user_id, user_profile_type, profile_configs, user_access_by_user_id, request_types_by_id):
            """
            Merge profile type permissions with user-specific access overrides.
            User-specific access is additive (extends profile type access).
            """
            # Start with profile type permissions
            profile_type = profile_configs.get(user_profile_type, ProfileTypeConfig())
            allowed_types = list(profile_type.permissions.get("allowed_request_types", []))
            blocked_types = list(profile_type.permissions.get("blocked_request_types", []))
            allowed_apis = list(profile_type.permissions.get("allowed_external_apis", []))
            
            # Apply user-specific access overrides if they exist
            if user_id in user_access_by_user_id:
                # User-specific overrides: add to allowed_request_types
                user_accesses = user_access_by_user_id[user_id]
                for access in user_accesses:
                    if access.is_active:  # Only include active access records
                        request_type_name = request_types_by_id.get(access.request_type_id)
                        if request_type_name and request_type_name not in allowed_types:
                            allowed_types.append(request_type_name)
            
            return {
                "allowed_request_types": allowed_types,
                "blocked_request_types": blocked_types,
                "allowed_external_apis": allowed_apis
            }
        
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
                    **merge_user_permissions(user.id, user.profile_type or "user", profile_configs, user_access_by_user_id, request_types_by_id),
                    "rate_limit_per_minute": profile_configs.get(user.profile_type).rate_limit_per_minute if user.profile_type in profile_configs else 10,
                    "rate_limit_per_hour": 100,
                    "rate_limit_per_day": 500,
                    "daily_request_limit": profile_configs.get(user.profile_type).daily_request_limit if user.profile_type in profile_configs else 100,
                    "monthly_request_limit": profile_configs.get(user.profile_type).monthly_request_limit if user.profile_type in profile_configs else 2000,
                    "priority": 5,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                }
                for user in users
            ],
            "exported_at": datetime.utcnow().isoformat(),
            "total_count": len(users),
        }
        
        filename = "latest.json"
        
        if export_type == "local":
            export_path = Path(config.get("local_path", "/app/exports/users"))
            if not export_path.exists():
                 export_path.mkdir(parents=True, exist_ok=True)
            
            latest_file = export_path / filename
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported users locally to {latest_file}")
            
        elif export_type == "ftp":
            host = config.get("ftp_host")
            user = config.get("ftp_user")
            passwd = config.get("ftp_password")
            port = int(config.get("ftp_port") or 21)
            # Use dedicated /users path for users export
            base_ftp_path = config.get("ftp_path", "/uploads")
            remote_path = "/users"  # Fixed path for user exports
            use_tls = config.get("ftp_use_tls", False)
            
            logger.info(f"Connecting to FTP: {host}:{port} as {user}")
            
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
                
                # Try to clean up messy simulated paths if they exist
                if remote_path == "/users/": # Handle trailing slash
                    remote_path = "/users"
                
                # Try to change to remote path
                try:
                    ftp.cwd(remote_path)
                except ftplib.error_perm:
                    logger.info(f"Path {remote_path} not found, trying to create...")
                    try:
                        ftp.mkd(remote_path)
                        ftp.cwd(remote_path)
                    except Exception as e:
                        logger.warning(f"Failed to create directory {remote_path}: {e}")
                        # Fallback to root if fails? No, keep raising or let it fail.
                
                ftp.storbinary(f"STOR {filename}", bio)
                ftp.quit()
                
                logger.info(f"Successfully uploaded {filename} to FTP server at {remote_path}")
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"FTP Upload failed: {e}\n{error_trace}")
                raise Exception(f"ftp_failed: {str(e)}\n{error_trace}")
        
        # Update last export timestamp in DB
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
        
        # Update SyncHistory
        sync_history.status = "success"
        sync_history.details = {"exported_count": len(users), "method": export_type}
        sync_history.completed_at = datetime.utcnow()
        session.commit()

        return {
            "status": "success",
            "exported_at": export_data["exported_at"],
            "total_count": len(users),
            "method": export_type
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"User export task failed: {e}\n{error_trace}")
        try:
            sync_history.status = "failed"
            sync_history.details = {"error": str(e), "traceback": error_trace}
            sync_history.completed_at = datetime.utcnow()
            session.commit()
        except:
            pass
        return {"status": "error", "reason": str(e)}
    finally:
        session.close()
