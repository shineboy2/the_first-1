"""
Export Requests Task - Export pending requests to response-network
"""
from datetime import datetime
import json
from pathlib import Path
import hashlib

from celery import shared_task
from sqlalchemy.orm import Session

from core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.request import Request as RequestModel
from models.user import User  # Register User model for relationship
from models.response import Response # Register Response model
import asyncio
from sqlalchemy import text


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

EXPORT_PATH = Path(settings.EXPORT_DIR) / "requests"


@shared_task(bind=True, max_retries=3)
def export_pending_requests(self):
    """
    Export all pending requests to file for response-network.
    
    Exports to: /exports/requests/requests_YYYYMMDD_HHMMSS.jsonl (or FTP path)
    
    Workflow:
    1. Query pending requests (status='pending')
    2. Sort by priority DESC, created_at ASC
    3. Generate JSONL file (JSON Lines format)
    4. Calculate SHA-256 checksum
    5. Write metadata file
    6. Update request status to 'exported'
    """
    try:
        # Get current timestamp for filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        batch_id = hashlib.sha256(timestamp.encode()).hexdigest()[:12]

        # Get synchronous session
        db = next(get_db_sync())

        try:
            # 0. Fetch Dynamic Settings specific for Export
            # Fetch 'export_config' blob directly
            settings_row = db.execute(text("SELECT value FROM settings WHERE key = 'export_config'")).fetchone()
            settings_dict = settings_row[0] if settings_row else {}
            
            # Construct Storage Config
            storage_config = {
                "type": settings_dict.get("type", "local"),
                "host": settings_dict.get("host", "localhost"),
                "port": int(settings_dict.get("port", 21)),
                "user": settings_dict.get("user", "anonymous"),
                "password": settings_dict.get("password", ""),
                "path": settings_dict.get("path", "/request-data/exports"),
                "use_tls": str(settings_dict.get("use_tls", "false")).lower() == "true"
            }
            
            # If local, ensure path is correct (Request Network usually maps /app/exports)
            if storage_config["type"] == "local":
                 storage_config["path"] = settings.EXPORT_DIR


            # 1. Query pending requests
            # Use joinedload to fetch user efficiently
            from sqlalchemy.orm import joinedload
            pending_requests = db.query(RequestModel).options(joinedload(RequestModel.user)).filter(
                RequestModel.status == "pending"
            ).order_by(
                RequestModel.priority.desc(),
                RequestModel.created_at.asc()
            ).limit(500).all()

            if not pending_requests:
                return {
                    "status": "no_changes",
                    "exported_at": datetime.utcnow().isoformat(),
                    "total_requests": 0
                }

            # 2. Prepare JSONL content
            jsonl_lines = []
            for req in pending_requests:
                jsonl_lines.append(json.dumps({
                    "id": str(req.id),
                    "user_id": str(req.user_id),
                    "username": req.user.username if req.user else "unknown",
                    "query_type": req.query_type,
                    "query_params": req.query_params or {},
                    "priority": req.priority,
                    "created_at": req.created_at.isoformat() if req.created_at else None,
                    "name": getattr(req, "name", None)
                }, ensure_ascii=False))
            
            file_data = "\n".join(jsonl_lines).encode("utf-8")
            
            # 3. Calculate checksum
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # 4. Save Main File using Storage Service
            from services.export_storage import ExportStorageService
            
            filename = f"requests_{timestamp}.jsonl"
            # Note: For FTP, path is handled by config['path'] + filename
            saved_path = asyncio.run(ExportStorageService.save_export_file(filename, file_data, storage_config))

            # 5. Save Metadata File
            metadata = {
                "batch_id": batch_id,
                "batch_type": "requests",
                "filename": filename,
                "file_size": len(file_data),
                "record_count": len(pending_requests),
                "checksum": file_hash,
                "exported_at": datetime.utcnow().isoformat(),
                "version": 1
            }
            meta_data_bytes = json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8')
            meta_filename = f"requests_{timestamp}.meta.json"
            saved_meta_path = asyncio.run(ExportStorageService.save_export_file(meta_filename, meta_data_bytes, storage_config))

            # 6. Update request status
            for req in pending_requests:
                req.status = "exported"
                req.exported_at = datetime.utcnow()
            
            db.commit()

            return {
                "status": "success",
                "export_file": saved_path,
                "metadata_file": saved_meta_path,
                "total_requests": len(pending_requests),
                "batch_id": batch_id,
                "checksum": file_hash,
                "exported_at": metadata["exported_at"],
            }
        finally:
            db.close()
            
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
