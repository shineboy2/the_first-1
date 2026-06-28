"""
Import Audit Logs ACKs Task - Read .ack files from response-network and delete local synced audit logs
"""
import ftplib
import io
import json
import logging
from pathlib import Path

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models.audit_log import AuditLog
from services.import_storage import ImportStorageService

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
def import_audit_acks(self):
    """
    Check for .ack / .nack files in the import path.
    If an ACK is found, mark those audit logs as synced and delete them.
    If a NACK is found, mark them as failed (or pending) for retry.
    """
    db = next(get_db_sync())
    try:
        config = ImportStorageService.get_import_config(db)
        if not config or not config.get("enabled", False):
            logger.info("Skipping audit ACKs import: configuration missing or disabled.")
            return {"status": "skipped", "reason": "config_missing"}

        import_type = config.get("storage_type", "local")
        
        ack_files = []
        nack_files = []
        
        if import_type == "local":
            base_path = Path(config.get("local_path", "/app/imports"))
            audit_logs_path = base_path / "audit_logs"
            if audit_logs_path.exists():
                for f in audit_logs_path.glob("*.ack"):
                    ack_files.append((f.name, f.read_text(encoding="utf-8")))
                    f.unlink()  # Delete the file after reading
                for f in audit_logs_path.glob("*.nack"):
                    nack_files.append((f.name, f.read_text(encoding="utf-8")))
                    f.unlink()

        elif import_type == "ftp":
            host = config.get("ftp_host")
            user = config.get("ftp_user")
            passwd = config.get("ftp_password")
            port = config.get("ftp_port", 21)
            remote_path = config.get("ftp_path", "/audit_logs")
            use_tls = config.get("ftp_use_tls", False)

            if not host:
                logger.error("FTP host missing in import_config for audit_logs")
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
                    # Directory doesn't exist yet
                    return {"status": "skipped", "reason": "no_directory"}

                files = ftp.nlst()
                for file_name in files:
                    if file_name.endswith(".ack") or file_name.endswith(".nack"):
                        bio = io.BytesIO()
                        ftp.retrbinary(f"RETR {file_name}", bio.write)
                        bio.seek(0)
                        content = bio.read().decode("utf-8")
                        
                        if file_name.endswith(".ack"):
                            ack_files.append((file_name, content))
                        else:
                            nack_files.append((file_name, content))
                            
                        # Delete the ACK/NACK file from FTP so we don't process it again
                        ftp.delete(file_name)

                try:
                    ftp.quit()
                except:
                    ftp.close()
            except Exception as e:
                logger.error(f"FTP ACK Download failed from {host}:{remote_path}: {e}")
                return {"status": "error", "reason": "ftp_error"}

        total_processed = 0
        total_deleted = 0
        
        # Process ACKs (Delete successful logs)
        for name, content in ack_files:
            try:
                data = json.loads(content)
                batch_id = data.get("batch_id")
                if batch_id:
                    # Find all logs with this batch_id and mark them as synced instead of deleting
                    # So they are kept for 7 days in the Request Network as per user requirement.
                    logs_to_update = db.query(AuditLog).filter(AuditLog.export_batch_id == batch_id).all()
                    for log in logs_to_update:
                        log.sync_status = "synced"
                        # total_deleted variable is now tracking total_synced
                        total_deleted += 1
                    total_processed += 1
            except Exception as e:
                logger.error(f"Error processing ACK file {name}: {e}")

        # Process NACKs (Reset to pending)
        for name, content in nack_files:
            try:
                data = json.loads(content)
                batch_id = data.get("batch_id")
                if batch_id:
                    # Find all logs with this batch_id and reset them
                    logs_to_reset = db.query(AuditLog).filter(AuditLog.export_batch_id == batch_id).all()
                    for log in logs_to_reset:
                        log.sync_status = "pending"
                        log.export_batch_id = None
                    total_processed += 1
            except Exception as e:
                logger.error(f"Error processing NACK file {name}: {e}")

        db.commit()

        return {
            "status": "success",
            "acks_processed": len(ack_files),
            "nacks_processed": len(nack_files),
            "logs_deleted": total_deleted
        }

    except Exception as exc:
        logger.error(f"Audit logs ACK import failed: {exc}")
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
