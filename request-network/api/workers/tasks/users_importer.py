"""
Users Importer Task - Import users from response-network (only if changed)
"""
from datetime import datetime
import json
from pathlib import Path
import hashlib
import os
from dotenv import load_dotenv

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Load .env
load_dotenv()

# Import User model
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.user import User as UserModel
# Import all models to resolve dependencies
from models.request import Request  # noqa
from models.response import Response  # noqa
from models.batch import ExportBatch, ImportBatch  # noqa
try:
    from models.api_key import ApiKey  # noqa
except ImportError:
    pass

# Import ImportStorageService
from services.import_storage import ImportStorageService
import logging

logger = logging.getLogger(__name__)

# Use shared_data directory from environment
SHARED_DATA_DIR = Path(os.getenv("SHARED_DATA_DIR", "/app/shared_data"))


@shared_task(bind=True, max_retries=3)
def import_users_from_response_network(self):
    """
    Import users from response-network.
    
    Workflow:
    1. Check /imports/users/ for latest.json
    2. Calculate checksum and compare with last imported
    3. If changed, import/update users
    4. Save checksum for next comparison
    
    This is a DELTA sync - only updates when files change.
    """
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
            # Determine paths using internal helper or config (for checksum storage)
            # Note: Checksums are stored locally relative to import path or in a fixed location
            # For simplicity in this phase, we use a fixed local path for tracking state
            PROCESSED_FILE = SHARED_DATA_DIR / "users" / ".processed_users"
            if not PROCESSED_FILE.parent.exists():
                PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
                
            # Use ImportStorageService to get data
            data = ImportStorageService.read_latest_file(db, "users")
            
            if not data:
                return {
                    "status": "skipped",
                    "message": "No data found or import_config missing",
                    "imported_at": datetime.utcnow().isoformat()
                }

            # Checksum logic
            current_checksum = hashlib.sha256(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()
            
            # Read previous checksum
            previous_checksum = None
            if PROCESSED_FILE.exists():
                try:
                    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
                        previous_data = json.load(f)
                        previous_checksum = previous_data.get("checksum")
                except Exception:
                    pass

            # If checksums match, no changes
            if previous_checksum and current_checksum == previous_checksum:
                return {
                    "status": "no_changes",
                    "message": "Users file has not changed",
                    "imported_at": datetime.utcnow().isoformat()
                }

            users_list = data.get("users", [])

            imported_count = 0
            updated_count = 0

            for user_data in users_list:
                user_id = user_data.get("id")
                
                # Try to find existing user by ID, username or email
                existing_user = db.query(UserModel).filter(
                    (UserModel.id == user_id) | 
                    (UserModel.username == user_data.get("username")) | 
                    (UserModel.email == user_data.get("email"))
                ).first()

                if existing_user:
                    # Update existing user
                    existing_user.username = user_data.get("username")
                    existing_user.email = user_data.get("email")
                    existing_user.hashed_password = user_data.get("hashed_password")
                    existing_user.full_name = user_data.get("full_name")
                    existing_user.is_active = user_data.get("is_active", True)
                    existing_user.profile_type = user_data.get("profile_type", "user")
                    existing_user.allowed_request_types = user_data.get("allowed_request_types", [])
                    existing_user.blocked_request_types = user_data.get("blocked_request_types", [])
                    existing_user.allowed_external_apis = user_data.get("allowed_external_apis", [])
                    existing_user.rate_limit_per_minute = user_data.get("rate_limit_per_minute", 10)
                    existing_user.rate_limit_per_hour = user_data.get("rate_limit_per_hour", 100)
                    existing_user.rate_limit_per_day = user_data.get("rate_limit_per_day", 500)
                    existing_user.daily_request_limit = user_data.get("daily_request_limit", 100)
                    existing_user.monthly_request_limit = user_data.get("monthly_request_limit", 2000)
                    existing_user.priority = user_data.get("priority", 5)
                    updated_count += 1
                else:
                    # Create new user
                    new_user = UserModel(
                        id=user_id,
                        username=user_data.get("username"),
                        email=user_data.get("email"),
                        hashed_password=user_data.get("hashed_password"),
                        full_name=user_data.get("full_name"),
                        is_active=user_data.get("is_active", True),
                        profile_type=user_data.get("profile_type", "user"),
                        allowed_request_types=user_data.get("allowed_request_types", []),
                        blocked_request_types=user_data.get("blocked_request_types", []),
                        allowed_external_apis=user_data.get("allowed_external_apis", []),
                        rate_limit_per_minute=user_data.get("rate_limit_per_minute", 10),
                        rate_limit_per_hour=user_data.get("rate_limit_per_hour", 100),
                        rate_limit_per_day=user_data.get("rate_limit_per_day", 500),
                        daily_request_limit=user_data.get("daily_request_limit", 100),
                        monthly_request_limit=user_data.get("monthly_request_limit", 2000),
                        priority=user_data.get("priority", 5)
                    )
                    db.add(new_user)
                    imported_count += 1

            db.commit()

            # Save new checksum
            with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "checksum": current_checksum,
                    "imported_at": datetime.utcnow().isoformat(),
                    "imported_count": imported_count,
                    "updated_count": updated_count
                }, f)

            return {
                "status": "success",
                "imported_count": imported_count,
                "updated_count": updated_count,
                "checksum": current_checksum,
                "imported_at": datetime.utcnow().isoformat()
            }
        finally:
            db.close()

    except Exception as exc:
        # Retry on error
        raise self.retry(exc=exc, countdown=60)
