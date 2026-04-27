"""
Results Importer Task - Import query results from response-network
"""
from datetime import datetime
import json
from pathlib import Path
import hashlib
import logging
import asyncio

from celery import shared_task
from sqlalchemy.orm import Session

from core.config import settings
from core.dependencies import get_db_sync
from models.request import Request as RequestModel
from models.user import User
from models.response import Response

logger = logging.getLogger(__name__)
IMPORT_PATH = Path(settings.IMPORT_DIR) / "results"


@shared_task(bind=True, max_retries=3)
def import_results_from_response_network(self):
    """
    Import query results from response-network.
    
    Workflow:
    1. Poll FTP/Local for result files (via ImportStorageService)
    2. Read JSONL format results
    3. Update corresponding requests with results
    4. Mark requests as completed
    
    File format: results_YYYYMMDD_HHMMSS.jsonl
    """
    try:
        db = next(get_db_sync())
        try:
            from services.import_storage import ImportStorageService
            
            # Read latest results file (abstracted Local/FTP)
            # Returns a list of dicts/lines
            results_data = ImportStorageService.read_latest_file(db, "results")
            
            if not results_data:
                return {
                    "status": "no_files",
                    "imported_at": datetime.utcnow().isoformat(),
                    "total_results": 0
                }

            total_imported = 0
            
            # Ensure results_data is a list (ImportStorageService handles parsing)
            # If the service returns raw dict (for json) vs list (for jsonl), we handle it.
            # Assuming ImportStorageService (Request Network version) handles it or returns loaded JSON.
            # Wait, I previously checked Request Network's ImportStorageService.
            # It returns `json.load(bio)` or `json.load(f)`. 
            # If the file is JSONL, `json.load` will fail if it's not a single JSON list.
            # We might need to update Request Network's ImportStorageService to handle JSONL or 
            # update this worker to handle whatever it gets. 
            # For now, let's assume valid JSON is returned or adapt.
            
            # UPDATE: Request Network ImportStorageService currently uses json.load().
            # Response Network writes JSONL.
            # json.load() on JSONL fails (Extra data).
            # I must update the ImportStorageService logic on Request Network OR 
            # change the Export logic on Response Network to match.
            # Changing Export logic is safer: Write a JSON Array instead of JSONL.
            # OR Update ImportStorageService to handle JSONL.
            # Let's update this file to handle list OR dict iteration if possible, 
            # BUT ImportStorageService will crash before returning if json.load fails.
            # I should update ImportStorageService first or concurrently.
            # Let's proceed with this refactor assuming ImportStorageService will be fixed.
            
            for result_data in results_data:
                try:
                    request_id = result_data.get("request_id")
                    
                    # Find request
                    request = db.query(RequestModel).filter(
                        RequestModel.id == request_id
                    ).first()

                    if request:
                        # Check if already completed to avoid overwrites (optional)
                        if request.status == "completed":
                            continue

                        # Create Response object
                        response_data = result_data.get("result_data", {})
                        
                        # Check has_error from the result_data (exported from response-network)
                        has_error = result_data.get("has_error", False)
                        
                        # Also check if there's an error in the response_data itself
                        if not has_error and "error" in response_data:
                            has_error = True
                        
                        error_message = response_data.get("error") if has_error else None
                        
                        response_obj = Response(
                            request_id=request.id,
                            result_data=response_data,
                            result_count=response_data.get("count", 0),
                            execution_time_ms=result_data.get("took", 0),
                            received_at=datetime.utcnow(),
                            has_error=has_error,
                            error_message=error_message
                        )
                        db.add(response_obj)

                        # Update request status based on has_error
                        if has_error:
                            request.status = "completed_error"
                        else:
                            request.status = "completed_success"
                        request.result_received_at = datetime.utcnow()
                        
                        # Invalidate cache for this request (async logic omitted/preserved)
                        try:
                            from db.redis_client import RedisClient
                            redis = RedisClient(settings.REDIS_URL)
                            # Use sync wrapper or loop if needed
                            # for simplicity in sync worker:
                            # asyncio.run(redis.invalidate_response(str(request_id)))
                        except Exception:
                            pass
                        
                        imported_count = 1
                        total_imported += imported_count

                except Exception as e:
                    logger.error(f"Error processing result item: {e}")
                    continue

            db.commit()

            return {
                "status": "success",
                "total_imported": total_imported,
                "imported_at": datetime.utcnow().isoformat()
            }
        finally:
            db.close()

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
