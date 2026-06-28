import json
import logging
from datetime import datetime
from pathlib import Path

from celery import shared_task

from core.config import settings
from core.dependencies import get_db_sync
from services.import_storage import ImportStorageService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def import_request_types_from_response_network(self):
    """
    Import request types definition from response network.
    Uses ImportStorageService to fetch 'request_types/latest.json'
    and writes it locally for the router to serve.
    """
    try:
        db = next(get_db_sync())
        try:
            # Note: We must ensure ImportStorageService knows how to fetch 'request_types'.
            # By default it will look for user_import_config if we pass resource_type="request_types",
            # unless we fallback to 'import_config' which is perfectly fine.
            data = ImportStorageService.read_latest_file(db, "request_types")
            
            if not data:
                return {
                    "status": "no_files",
                    "imported_at": datetime.utcnow().isoformat(),
                }
            
            # Ensure local directory exists
            local_path = Path(settings.IMPORT_DIR) / "request_types"
            local_path.mkdir(parents=True, exist_ok=True)
            
            # Write out to latest.json for the router
            file_path = local_path / "latest.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Successfully imported request types to {file_path}")
            
            return {
                "status": "success",
                "imported_at": datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Failed to import request types: {exc}")
        raise self.retry(exc=exc, countdown=60)
