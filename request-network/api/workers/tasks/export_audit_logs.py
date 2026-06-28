"""
Export Audit Logs Task - Export pending audit logs to response-network (Sync version)
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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models.audit_log import AuditLog
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

@shared_task(bind=True, max_retries=3)
def export_audit_logs(self):
    """
    Export all pending audit logs to response-network.
    Uses synchronous logic to avoid asyncio issues in Celery.
    """
    db = next(get_db_sync())
    try:
        # 0. Fetch Dynamic Settings
        config_setting = db.query(SettingsModel).filter(SettingsModel.key == "export_config").first()
            
        if not config_setting or not config_setting.value:
            logger.info("Skipping audit logs export: configuration missing.")
            return {"status": "skipped", "reason": "config_missing"}
            
        export_config = config_setting.value
        
        if not export_config.get("enabled", False):
             logger.info("Export is disabled.")
             return {"status": "skipped", "reason": "disabled"}

        # 1. Query pending audit logs
        pending_logs = db.query(AuditLog).filter(
            AuditLog.sync_status == "pending"
        ).order_by(
            AuditLog.id.asc()
        ).limit(1000).all()

        if not pending_logs:
            return {
                "status": "no_changes",
                "exported_at": datetime.utcnow().isoformat(),
                "total_logs": 0
            }

        # Get current timestamp for filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        batch_id = str(uuid.uuid4())

        # 2. Prepare JSONL content
        jsonl_lines = []
        for log_entry in pending_logs:
            # We must serialize UUIDs and datetime
            jsonl_lines.append(json.dumps({
                "id": log_entry.id,
                "user_id": str(log_entry.user_id) if log_entry.user_id else None,
                "action": log_entry.action,
                "resource_type": log_entry.resource_type,
                "resource_id": log_entry.resource_id,
                "ip_address": log_entry.ip_address,
                "user_agent": log_entry.user_agent,
                "request_data": log_entry.request_data,
                "response_status": log_entry.response_status,
                "meta": log_entry.meta,
                "created_at": log_entry.created_at.isoformat() if log_entry.created_at else None
            }, ensure_ascii=False))
        
        file_data = "\n".join(jsonl_lines)
        file_bytes = file_data.encode("utf-8")
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        
        filename = f"audit_logs_{timestamp}.jsonl"
        meta_filename = f"audit_logs_{timestamp}.meta.json"
        
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
            "batch_type": "audit_logs",
            "filename": filename,
            "file_size": len(file_bytes),
            "record_count": len(pending_logs),
            "checksum": file_hash,
            "exported_at": datetime.utcnow().isoformat(),
            "version": 1
        }
        meta_bytes = json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8')

        if export_type == "local":
            local_path = Path(export_config.get("local_path", "/app/exports/audit_logs"))
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
            
            logger.info(f"Exported audit logs locally to {saved_path}")

        elif export_type == "ftp":
            host = export_config.get("ftp_host")
            user = export_config.get("ftp_user")
            passwd = export_config.get("ftp_password")
            port = export_config.get("ftp_port", 21)
            remote_path = export_config.get("ftp_path", "/audit_logs")
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
            logger.info(f"Exported audit logs to FTP: {saved_path}")

        # 4. Update audit log status
        for log_entry in pending_logs:
            log_entry.sync_status = "exported"
            log_entry.export_batch_id = batch_id
        
        db.commit()

        return {
            "status": "success",
            "export_file": saved_path,
            "metadata_file": saved_meta_path,
            "total_logs": len(pending_logs),
            "batch_id": batch_id,
            "checksum": file_hash,
            "exported_at": metadata["exported_at"],
        }

    except Exception as exc:
        logger.error(f"Audit logs export failed: {exc}")
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
