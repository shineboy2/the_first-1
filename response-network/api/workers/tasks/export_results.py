from datetime import datetime
import json
from pathlib import Path
import os
import uuid

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models.incoming_request import IncomingRequest
from models.query_result import QueryResult

# Setup sync database connection for Celery
sync_engine = create_engine(
    str(settings.DATABASE_URL).replace('postgresql+asyncpg', 'postgresql'),
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

EXPORT_PATH = Path(settings.EXPORT_DIR) / "results"

@shared_task(bind=True, max_retries=3)
def export_completed_results(self):
    """Export completed request results to request network."""
    import asyncio
    from services.export_storage import ExportStorageService
    from models.settings import Settings as SettingsModel

    db = SessionLocal()
    try:
        # Get dynamic export config
        config_setting = db.query(SettingsModel).filter(SettingsModel.key == "export_config").first()
        export_config = config_setting.value if config_setting else None

        # Get results that haven't been exported
        results = db.query(QueryResult).join(IncomingRequest).filter(
            QueryResult.exported_at.is_(None)
        ).limit(50).all()
        
        if not results:
            return {"status": "no_new_results", "count": 0}
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        batch_id = uuid.uuid4()
        
        # Prepare export data
        export_list = []
        for res in results:
            export_list.append({
                "request_id": str(res.original_request_id), # Map back to original ID for Request Network
                "status": "completed",
                "result_data": res.result_data,
                "execution_time_ms": res.execution_time_ms,
                "executed_at": res.executed_at.isoformat() if res.executed_at else None,
                "exported_at": datetime.utcnow().isoformat()
            })
            
        # Write to JSONL string/bytes
        jsonl_content = ""
        for item in export_list:
            jsonl_content += json.dumps(item) + "\n"
        
        filename = f"results_{timestamp}.jsonl"
        
        # Execute async storage save
        saved_path = asyncio.run(
            ExportStorageService.save_export_file(
                filename, 
                jsonl_content.encode("utf-8"), 
                export_config
            )
        )
        
        # Mark as exported
        for res in results:
            res.exported_at = datetime.utcnow()
            res.export_batch_id = batch_id
            
        db.commit()
        
        return {
            "status": "success",
            "count": len(results),
            "file": saved_path,
            "batch_id": str(batch_id)
        }
            
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()