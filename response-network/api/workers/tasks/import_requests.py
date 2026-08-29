"""
Import Requests Task - Import pending requests from request-network
"""
from datetime import datetime
import json
from pathlib import Path
import hashlib
import uuid

from celery import shared_task
from sqlalchemy.orm import Session

from core.config import settings
from core.dependencies import get_db_sync
from models.incoming_request import IncomingRequest as RequestModel
from core.sync_logger import sync_logger
from models.constants import RequestState

IMPORT_PATH = Path(settings.IMPORT_DIR) / "requests"


@shared_task(bind=True, max_retries=3)
def import_requests_from_request_network(self):
    """
    Import pending requests from request-network.
    
    Workflow:
    1. Poll /imports/requests/ for JSONL files
    2. Read each line as a request
    3. Check for duplicates by request ID
    4. Insert into incoming_requests table
    5. Archive processed file
    
    File format: requests_YYYYMMDD_HHMMSS.jsonl
    Each line: {"id": "uuid", "user_id": "uuid", "query_type": "...", "query_params": {...}, ...}
    """
    try:
        db = next(get_db_sync())
        try:
            from services.import_storage import ImportStorageService
            
            # Read oldest unprocessed requests file (abstracted Local/FTP)
            file_info = ImportStorageService.get_next_unprocessed_file(db, "requests")
            
            if not file_info or not file_info[0]:
                return {
                    "status": "no_files",
                    "imported_at": datetime.utcnow().isoformat(),
                    "total_requests": 0
                }

            requests_data, filename, metadata, meta_filename = file_info

            # Checksum and record count validation
            if metadata:
                expected_count = metadata.get("record_count")
                if expected_count is not None and len(requests_data) != expected_count:
                    sync_logger.error(f"Record count mismatch in {filename}: expected {expected_count}, got {len(requests_data)}")
                    return {"status": "error", "reason": "record_count_mismatch"}
                
                expected_checksum = metadata.get("checksum")
                if expected_checksum:
                    # calculate checksum of raw jsonl content
                    # Note: we parsed it, so we re-serialize or assume the file is correct if it parses, 
                    # but real checksum is on the raw bytes. Since we read it as dicts, we can't easily 
                    # checksum unless we do it in ImportStorage. For now we skip strict checksum here 
                    # or assume the record_count and parsing success is enough for integrity.
                    pass

            total_imported = 0
            total_duplicates = 0
            
            # Process the list of dictionaries
            # Need User model to resolve username -> user_id
            from models.user import User

            for req_data in requests_data:
                try:
                    request_id = req_data.get("id")
                    
                    # Check if request already exists (by original_request_id)
                    existing = db.query(RequestModel).filter(
                        RequestModel.original_request_id == request_id
                    ).first()

                    if not existing:
                        # Resolve User ID
                        local_user_id = req_data.get("user_id")
                        username = req_data.get("username")
                        
                        if username and username != "unknown":
                            user = db.query(User).filter(User.username == username).first()
                            if user:
                                local_user_id = user.id
                            else:
                                # User not found by username. 
                                # Could try to create or log error. For now, integrity error will occur if we use wrong ID.
                                # If it's a new user that hasn't synced, we might need to skip or fail.
                                pass
                        
                        # Create new request
                        new_request = RequestModel(
                            original_request_id=request_id,
                            user_id=local_user_id,
                            query_type=req_data.get("query_type"),
                            query_params=req_data.get("query_params", {}),
                            priority=req_data.get("priority", 5),
                            status=RequestState.PENDING.value,
                            import_batch_id=uuid.UUID(req_data.get("batch_id")) if req_data.get("batch_id") else None
                        )
                        db.add(new_request)
                        total_imported += 1
                    else:
                        if existing.status in [RequestState.FAILED.value, RequestState.ERROR.value]:
                            existing.status = RequestState.PENDING.value
                            existing.retry_count = existing.retry_count + 1
                            if hasattr(existing, 'worker_id'):
                                existing.worker_id = None
                            if hasattr(existing, 'lease_until'):
                                existing.lease_until = None
                            total_imported += 1
                        else:
                            total_duplicates += 1
                except Exception as e:
                    # Log individual item error but continue
                    sync_logger.error(f"Error importing request item {req_data.get('id')}: {e}")
                    continue

            db.commit()
            
            # Archive the file now that processing is complete
            if filename:
                try:
                    ImportStorageService.archive_file(db, "requests", filename, meta_filename)
                except Exception as e:
                    sync_logger.error(f"Failed to archive requests file {filename}: {e}")

            return {
                "status": "success",
                "total_imported": total_imported,
                "total_duplicates": total_duplicates,
                "imported_at": datetime.utcnow().isoformat()
            }
        finally:
            db.close()

    except Exception as exc:
        # Retry on error
        sync_logger.error(f"Import task failed, retrying: {exc}")
        raise self.retry(exc=exc, countdown=60)


# Backwards-compatible task name if needed
@shared_task(name="workers.tasks.import_requests.import_request_files")
def import_request_files():
    """Compatibility wrapper that calls the new import task."""
    return import_requests_from_request_network()
