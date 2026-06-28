"""
Import Audit Logs Task - Read .jsonl files from request-network, import to DB, and send ACK
"""
import ftplib
import io
import json
import logging
from datetime import datetime
import asyncio
from pathlib import Path

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models.audit_log import AuditLog
from services.import_storage import ImportStorageService
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

def send_ack_sync(db, batch_id: str, success: bool = True):
    """
    Synchronously upload an ACK or NACK file to the export config FTP.
    Since we are in a celery worker, we use synchronous ftplib instead of the async ExportStorageService.
    """
    try:
        config_setting = db.query(SettingsModel).filter(SettingsModel.key == "export_config").first()
        if not config_setting or not config_setting.value:
            logger.warning("No export_config found, cannot send ACK/NACK.")
            return

        export_config = config_setting.value
        export_type = export_config.get("type", "local")
        
        ext = "ack" if success else "nack"
        filename = f"audit_batch_{batch_id}.{ext}"
        
        data = {
            "batch_id": batch_id,
            "status": "success" if success else "failed",
            "timestamp": datetime.utcnow().isoformat()
        }
        file_bytes = json.dumps(data).encode("utf-8")

        if export_type == "local":
            local_path = Path(export_config.get("path", "/app/exports")) / "audit_logs"
            local_path.mkdir(parents=True, exist_ok=True)
            with open(local_path / filename, "wb") as f:
                f.write(file_bytes)
            logger.info(f"Local {ext.upper()} saved: {filename}")
            
        elif export_type == "ftp":
            host = export_config.get("host")
            user = export_config.get("user")
            passwd = export_config.get("password")
            port = export_config.get("port", 21)
            remote_path = export_config.get("path", "/audit_logs")
            use_tls = export_config.get("use_tls", False)
            
            if not host:
                logger.warning(f"FTP host missing in export_config, cannot send {ext.upper()}")
                return
                
            bio = io.BytesIO(file_bytes)
            
            if use_tls:
                ftp = ftplib.FTP_TLS()
            else:
                ftp = ftplib.FTP()
                
            ftp.connect(host, port)
            ftp.login(user=user, passwd=passwd)
            
            try:
                ftp.cwd(remote_path)
            except:
                ftp.mkd(remote_path)
                ftp.cwd(remote_path)
                
            ftp.storbinary(f"STOR {filename}", bio)
            ftp.quit()
            logger.info(f"FTP {ext.upper()} sent to {host}:{remote_path}/{filename}")
            
    except Exception as e:
        logger.error(f"Failed to send ACK/NACK for batch {batch_id}: {e}")

@shared_task(bind=True, max_retries=3)
def import_audit_logs(self):
    """
    Import audit logs from request-network.
    Uses synchronous logic to avoid asyncio issues in Celery.
    """
    db = next(get_db_sync())
    try:
        # We need to list all files from ImportStorageService for audit_logs
        # Since ImportStorageService.read_latest_file only reads the latest,
        # we write custom FTP retrieval here to process ALL pending files, like import_results does.
        
        config = ImportStorageService.get_import_config(db, "audit_logs")
        if not config:
             logger.info("Skipping audit logs import: configuration missing.")
             return {"status": "skipped", "reason": "config_missing"}

        import_type = config.get("storage_type", config.get("type", "local"))
        
        processed_files = []
        files_data = [] # List of tuples: (filename, [logs])
        
        if import_type == "local":
            base_path = Path(config.get("local_path", config.get("path", "/app/imports")))
            audit_logs_path = base_path / "audit_logs"
            if audit_logs_path.exists():
                for file_path in audit_logs_path.glob("*.jsonl"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        logs = [json.loads(line) for line in lines if line.strip()]
                        files_data.append((file_path.name, logs))
                        file_path.unlink() # Delete after reading
                        
        elif import_type == "ftp":
            host = config.get("ftp_host", config.get("host"))
            user = config.get("ftp_user", config.get("user"))
            passwd = config.get("ftp_password", config.get("password"))
            port = config.get("ftp_port", config.get("port", 21))
            remote_path = config.get("ftp_path", config.get("path", "/audit_logs"))
            use_tls = config.get("ftp_use_tls", config.get("use_tls", False))
            
            if not host:
                return {"status": "error", "reason": "ftp_host_missing"}
            
            try:
                if use_tls:
                    ftp = ftplib.FTP_TLS()
                    ftp.connect(host, port)
                    ftp.login(user=user, passwd=passwd)
                    ftp.prot_p()
                else:
                    ftp = ftplib.FTP()
                    ftp.connect(host, port)
                    ftp.login(user=user, passwd=passwd)
                
                try:
                    ftp.cwd(remote_path)
                except:
                    # Directory not found
                    return {"status": "skipped", "reason": "no_directory"}
                
                files = ftp.nlst()
                jsonl_files = [f for f in files if f.endswith(".jsonl")]
                
                for filename in jsonl_files:
                    bio = io.BytesIO()
                    ftp.retrbinary(f"RETR {filename}", bio.write)
                    bio.seek(0)
                    lines = bio.getvalue().decode('utf-8').splitlines()
                    logs = [json.loads(line) for line in lines if line.strip()]
                    files_data.append((filename, logs))
                    
                    # Delete file from incoming FTP after reading
                    ftp.delete(filename)
                
                try:
                    ftp.quit()
                except:
                    ftp.close()
            except Exception as e:
                logger.error(f"FTP Audit Logs download failed: {e}")
                return {"status": "error", "reason": "ftp_error"}
                
        total_imported = 0
        
        for filename, logs in files_data:
            batch_id = None
            try:
                for log_data in logs:
                    if not batch_id and "id" in log_data: # Just fallback
                        pass
                        
                    # Check if log already exists by some constraint if needed, but since id is from request-network,
                    # we should not overwrite id, we generate a new ID in response network, or we map it.
                    # It's better to auto-increment and store original id in meta or just insert.
                    
                    new_log = AuditLog(
                        user_id=log_data.get("user_id"),
                        action=log_data.get("action"),
                        resource_type=log_data.get("resource_type"),
                        resource_id=log_data.get("resource_id"),
                        ip_address=log_data.get("ip_address"),
                        user_agent=log_data.get("user_agent"),
                        request_data=log_data.get("request_data"),
                        response_status=log_data.get("response_status"),
                        meta=log_data.get("meta"),
                        created_at=datetime.fromisoformat(log_data.get("created_at")) if log_data.get("created_at") else datetime.utcnow()
                    )
                    db.add(new_log)
                    total_imported += 1
                
                # Retrieve batch_id from the metadata file or filename if possible
                # Wait, we exported meta file with batch_id. But since we didn't read meta file, 
                # let's extract timestamp or name from filename as pseudo batch_id if not present.
                # In export_audit_logs, we did:
                # filename = f"audit_logs_{timestamp}.jsonl"
                batch_id = filename.replace("audit_logs_", "").replace(".jsonl", "")
                
                db.commit()
                processed_files.append(filename)
                
                # Send ACK
                send_ack_sync(db, batch_id, success=True)
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error importing file {filename}: {e}")
                if batch_id:
                    # Send NACK
                    send_ack_sync(db, batch_id, success=False)
                
        return {
            "status": "success",
            "files_processed": len(processed_files),
            "total_imported": total_imported
        }
        
    except Exception as exc:
        logger.error(f"Audit logs import failed: {exc}")
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
