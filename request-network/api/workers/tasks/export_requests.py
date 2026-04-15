"""
Export Requests Task - Export pending requests to response-network (Sync version)
"""
from datetime import datetime
import json
from pathlib import Path
import hashlib
import io
import ftplib
import logging
import uuid

from celery import shared_task
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, joinedload

from core.config import settings
from models.request import Request as RequestModel
from models.user import User
from models.settings import Settings as SettingsModel

logger = logging.getLogger(__name__)

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
    Export all pending requests to response-network.
    Uses synchronous logic to avoid asyncio issues in Celery.
    """
    db = next(get_db_sync())
    try:
        # 0. Fetch Dynamic Settings
        # Priority: request_export_config > export_config
        config_setting = db.query(SettingsModel).filter(SettingsModel.key == "request_export_config").first()
        if not config_setting:
            config_setting = db.query(SettingsModel).filter(SettingsModel.key == "export_config").first()
            
        if not config_setting or not config_setting.value:
            logger.info("Skipping request export: configuration missing.")
            return {"status": "skipped", "reason": "config_missing"}
            
        export_config = config_setting.value
        
        if not export_config.get("enabled", False):
             logger.info("Request export is disabled.")
             return {"status": "skipped", "reason": "disabled"}

        # 1. Query pending requests
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


        # Get current timestamp for filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        batch_id = str(uuid.uuid4())

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
        
        file_data = "\n".join(jsonl_lines)
        file_bytes = file_data.encode("utf-8")
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        
        filename = f"requests_{timestamp}.jsonl"
        meta_filename = f"requests_{timestamp}.meta.json"
        
        # 3. Save Files
        export_type = export_config.get("storage_type", "local")
        # Fallback for old config format
        if "storage_type" not in export_config and "destination_type" in export_config:
            export_type = export_config["destination_type"]
            
        saved_path = ""
        saved_meta_path = ""
        
        # Metadata
        metadata = {
            "batch_id": batch_id,
            "batch_type": "requests",
            "filename": filename,
            "file_size": len(file_bytes),
            "record_count": len(pending_requests),
            "checksum": file_hash,
            "exported_at": datetime.utcnow().isoformat(),
            "version": 1
        }
        meta_bytes = json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8')

        if export_type == "local":
            local_path = Path(export_config.get("local_path", "/app/exports/requests"))
            if not local_path.exists():
                local_path.mkdir(parents=True, exist_ok=True)
            
            # Save Data File
            file_path = local_path / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_data)
            saved_path = str(file_path)
            
            # Save Meta File
            meta_path = local_path / meta_filename
            with open(meta_path, "wb") as f:
                f.write(meta_bytes)
            saved_meta_path = str(meta_path)
            
            logger.info(f"Exported requests locally to {saved_path}")

        elif export_type == "ftp":
            host = export_config.get("ftp_host")
            user = export_config.get("ftp_user")
            passwd = export_config.get("ftp_password")
            port = export_config.get("ftp_port", 21)
            remote_path = export_config.get("ftp_path", "/requests")
            use_tls = export_config.get("ftp_use_tls", False)
            
            if not host:
                raise ValueError("FTP host not configured")

            bio_data = io.BytesIO(file_bytes)
            bio_meta = io.BytesIO(meta_bytes)
            
            if use_tls:
                ftp = ftplib.FTP_TLS()
            else:
                ftp = ftplib.FTP()
            
            logger.info(f"Connecting to FTP {host}:{port}")
            ftp.connect(host, port)
            ftp.login(user=user, passwd=passwd)
            
            try:
                ftp.cwd(remote_path)
            except:
                logger.info(f"Creating directory {remote_path}")
                try:
                    ftp.mkd(remote_path)
                    ftp.cwd(remote_path)
                except Exception as e:
                    logger.warning(f"Failed to create/cwd to {remote_path}: {e}")
            
            # Upload files
            ftp.storbinary(f"STOR {filename}", bio_data)
            ftp.storbinary(f"STOR {meta_filename}", bio_meta)
            
            ftp.quit()
            saved_path = f"ftp://{host}/{remote_path}/{filename}"
            saved_meta_path = f"ftp://{host}/{remote_path}/{meta_filename}"
            logger.info(f"Exported requests to FTP: {saved_path}")

        # 4. Update request status
        for req in pending_requests:
            req.status = "exported"
            req.exported_at = datetime.utcnow()
            req.export_batch_id = batch_id
        
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

    except Exception as exc:
        logger.error(f"Request export failed: {exc}")
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
