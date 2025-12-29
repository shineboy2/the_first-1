from datetime import datetime
import json
from pathlib import Path

from celery import shared_task
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from core.config import settings
from services.import_storage import ImportStorageService
from models.settings import Settings
from models.user import User
from schemas.settings import SettingsImport

# Setup sync database connection for Celery
sync_engine = create_engine(
    str(settings.DATABASE_URL).replace('postgresql+asyncpg', 'postgresql+psycopg'),
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def get_db_sync():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

PASSWORD_CHANGES_PATH = Path(settings.EXPORT_DIR) / "password_changes"

@shared_task
def import_settings_from_response_network():
    """
    Import settings from response network.
    
    Uses ImportStorageService to support FTP.
    Wait for configuration if not set.
    """
    results = {
        "settings_imported": 0,
        "passwords_synced": 0,
        "errors": [],
        "status": "pending"
    }

    db = next(get_db_sync())
    try:
        # ============ IMPORT SETTINGS ============
        try:
            # Use Service to read file (supports FTP)
            data = ImportStorageService.read_latest_file(db, "settings")
            
            if data is None:
                results["status"] = "skipped"
                results["message"] = "Waiting for configuration or file not found"
                return results

            import_data = SettingsImport(**data)
            
            # For each imported setting
            for setting in import_data.settings:
                # Check if setting already exists
                existing = db.query(Settings).filter(Settings.key == setting.key).first()
                
                if existing:
                    # Update existing setting
                    existing.value = setting.value
                    existing.description = setting.description
                    existing.is_active = True
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new setting
                    new_setting = Settings(
                        key=setting.key,
                        value=setting.value,
                        description=setting.description,
                        is_active=True,
                    )
                    db.add(new_setting)
            
            db.commit()
            results["settings_imported"] = len(import_data.settings)
            results["status"] = "success"

        except Exception as e:
            results["errors"].append(f"Settings import error: {str(e)}")
            results["status"] = "error"
        
        # ============ AUTO-SYNC PASSWORD CHANGES ============
        # (This part relies on local file for now, assuming password changes are also synced via FTP eventually)
        # For now, we keep existing logic but wrapped in sync session
        
        try:
            queue_file = PASSWORD_CHANGES_PATH / "password_changes_queue.json"
            
            if queue_file.exists():
                with open(queue_file, "r") as f:
                    password_changes = json.load(f)
                
                if not isinstance(password_changes, list):
                    password_changes = [password_changes]
                
                for change in password_changes:
                    try:
                        user_id = change.get("user_id")
                        hashed_password = change.get("hashed_password")
                        username = change.get("username")
                        
                        if not user_id or not hashed_password:
                            continue
                        
                        user = db.query(User).filter(User.id == user_id).first()
                        
                        if not user:
                            results["errors"].append(f"User {username} ({user_id}) not found")
                            continue
                        
                        user.hashed_password = hashed_password
                        user.synced_at = datetime.utcnow()
                        db.add(user)
                        results["passwords_synced"] += 1
                        
                    except Exception as e:
                        results["errors"].append(f"Error syncing password: {str(e)}")
                
                db.commit()
                
                if results["passwords_synced"] > 0:
                    queue_file.unlink()
                    
        except FileNotFoundError:
            pass
        except Exception as e:
            results["errors"].append(f"Password sync error: {str(e)}")
        
        # Return summary
        message = f"✅ Settings: {results['settings_imported']}, Passwords: {results['passwords_synced']}"
        if results["errors"]:
            message += f" | ⚠️ {len(results['errors'])} errors"
        
        results["message"] = message
        results["timestamp"] = datetime.utcnow().isoformat()
        
        return results

    finally:
        db.close()