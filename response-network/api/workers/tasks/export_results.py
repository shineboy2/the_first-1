from datetime import datetime
import json
from pathlib import Path
import os
import uuid
import ftplib
import io
import logging

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models.incoming_request import IncomingRequest
from models.query_result import QueryResult
from models.settings import Settings as SettingsModel

logger = logging.getLogger(__name__)

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
    db = SessionLocal()
    try:
        # Get dynamic export config
        config_setting = db.query(SettingsModel).filter(SettingsModel.key == "result_export_config").first()
        
        # Fallback to general export_config if specific one not found (for backward compatibility)
        if not config_setting:
             config_setting = db.query(SettingsModel).filter(SettingsModel.key == "export_config").first()

        if not config_setting or not config_setting.value:
            logger.info("Skipping result export: configuration missing.")
            return {"status": "skipped", "reason": "config_missing"}

        export_config = config_setting.value
        
        if not export_config.get("enabled", False):
             logger.info("Result export is disabled.")
             return {"status": "skipped", "reason": "disabled"}

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
                "request_id": str(res.original_request_id),  # Map back to original ID for Request Network
                "status": "completed",
                "result_data": res.result_data,
            })
            
        # Write to JSONL string/bytes
        jsonl_content = ""
        for item in export_list:
            jsonl_content += json.dumps(item) + "\n"
        
        filename = f"results_{timestamp}.jsonl"
        export_type = export_config.get("storage_type", "local") # Use "storage_type" to match new config format
        
        # Fallback to "destination_type" if "storage_type" missing (key name changed in different versions)
        if "storage_type" not in export_config and "destination_type" in export_config:
            export_type = export_config["destination_type"]
            
        saved_path = ""

        if export_type == "local":
            local_path = Path(export_config.get("local_path", "/app/exports/results"))
            if not local_path.exists():
                local_path.mkdir(parents=True, exist_ok=True)
            
            file_path = local_path / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(jsonl_content)
            saved_path = str(file_path)
            logger.info(f"Exported results locally to {saved_path}")

        elif export_type == "ftp":
            host = export_config.get("ftp_host")
            user = export_config.get("ftp_user")
            passwd = export_config.get("ftp_password")
            port = export_config.get("ftp_port") or 21
            remote_path = export_config.get("ftp_path", "/results")
            use_tls = export_config.get("ftp_use_tls", False)
            
            if not host:
                raise ValueError("FTP host not configured")

            bio = io.BytesIO(jsonl_content.encode('utf-8'))
            
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
            
            ftp.storbinary(f"STOR {filename}", bio)
            ftp.quit()
            saved_path = f"ftp://{host}/{remote_path}/{filename}"
            logger.info(f"Exported results to FTP: {saved_path}")

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
        logger.error(f"Result export failed: {exc}")
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()