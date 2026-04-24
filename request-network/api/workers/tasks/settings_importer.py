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
    
    DISABLED: Settings import is no longer needed as request-network manages its own settings.
    User data and access controls are imported via users_importer.py instead.
    """
    return {
        "status": "disabled",
        "message": "Settings import has been deprecated. User data including permissions is imported via users_importer.py",
        "settings_imported": 0,
        "passwords_synced": 0,
        "errors": []
    }