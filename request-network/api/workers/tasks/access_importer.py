"""
Access Importer Task - Import user and profile type access from response-network
"""
from datetime import datetime
import json
from pathlib import Path
import logging
import os
from dotenv import load_dotenv

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Load .env
load_dotenv()

logger = logging.getLogger(__name__)

# Import models
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.user import User as UserModel
from models.request import Request  # noqa

# Import ImportStorageService
from services.import_storage import ImportStorageService


@shared_task(bind=True, max_retries=3)
def import_access_from_response_network(self):
    """
    Import user and profile type access from response-network.
    
    DISABLED: Access control is now included in users_importer.py.
    User permissions, blocked/allowed request types, and rate limits are imported
    as part of the user import data.
    """
    return {
        "status": "disabled",
        "message": "Access import has been consolidated into users_importer.py to avoid redundancy"
    }
    try:
        # Build database URL from env
        db_user = os.getenv("REQUEST_DB_USER", "user")
        db_pass = os.getenv("REQUEST_DB_PASSWORD", "password")
        db_host = os.getenv("REQUEST_DB_HOST", "postgres-request-db")
        db_port = os.getenv("REQUEST_DB_PORT", "5432")
        db_name = os.getenv("REQUEST_DB_NAME", "request_db")
        
        database_url = f"postgresql+psycopg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        
        # Create sync engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        try:
            # Use ImportStorageService to get data
            data = ImportStorageService.read_latest_file(db, "access")
            
            if not data:
                return {
                    "status": "skipped",
                    "message": "No access data found or import_config missing",
                    "imported_at": datetime.utcnow().isoformat()
                }

            user_access_list = data.get("user_access", [])
            profile_access_list = data.get("profile_type_access", [])

            # Step 1: Import user-level access
            updated_users = {}
            
            for access in user_access_list:
                user_id = access.get("user_id")
                request_type_name = access.get("request_type_name")
                is_active = access.get("is_active", True)
                
                if not user_id or not request_type_name:
                    continue
                
                if user_id not in updated_users:
                    updated_users[user_id] = {
                        "allowed_request_types": [],
                        "blocked_request_types": []
                    }
                
                if is_active:
                    updated_users[user_id]["allowed_request_types"].append(request_type_name)
                else:
                    updated_users[user_id]["blocked_request_types"].append(request_type_name)
            
            # Update users with their access
            imported_count = 0
            for user_id, access_data in updated_users.items():
                user = db.query(UserModel).filter(UserModel.id == user_id).first()
                
                if user:
                    user.allowed_request_types = access_data["allowed_request_types"]
                    user.blocked_request_types = access_data["blocked_request_types"]
                    db.add(user)
                    imported_count += 1
            
            db.commit()
            
            # Step 2: Log profile type access (for reference only, not stored per-user)
            logger.info(f"Profile Type Access: {len(profile_access_list)} records imported")
            
            return {
                "status": "success",
                "message": f"✅ Updated {imported_count} users with access permissions",
                "user_access_count": len(user_access_list),
                "profile_access_count": len(profile_access_list),
                "imported_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Access import failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"❌ Access import failed: {str(e)}",
                "imported_at": datetime.utcnow().isoformat()
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Task setup failed: {str(e)}", exc_info=True)
        # Retry task
        raise self.retry(exc=e, countdown=60, max_retries=3)
