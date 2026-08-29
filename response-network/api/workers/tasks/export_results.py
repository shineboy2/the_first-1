from datetime import datetime
import json
import hashlib
from pathlib import Path
import os
import uuid
import ftplib
import io
import logging

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.encryption import encrypt_data

from core.config import settings
from models.incoming_request import IncomingRequest
from models.query_result import QueryResult
from models.settings import Settings as SettingsModel
from models.sync_history import SyncHistory
from models.ftp_profile import FTPProfile
from models.constants import RequestState

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
            
        sync_history = SyncHistory(
            operation_type="result_export",
            status="in_progress"
        )
        db.add(sync_history)
        db.commit()
        db.refresh(sync_history)

        export_config = config_setting.value
        
        if not export_config.get("enabled", False):
             logger.info("Result export is disabled.")
             return {"status": "skipped", "reason": "disabled"}

        # Get results that haven't been exported
        # Use SKIP LOCKED to avoid multiple workers picking up the same results
        results = db.query(QueryResult).join(IncomingRequest).filter(
            QueryResult.exported_at.is_(None)
        ).with_for_update(skip_locked=True, of=QueryResult).limit(50).all()
        
        if not results:
            sync_history.status = "skipped"
            sync_history.details = {"reason": "no_new_results"}
            sync_history.completed_at = datetime.utcnow()
            db.commit()
            return {"status": "no_new_results", "count": 0}
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        batch_id = uuid.uuid4()
        
        # Prepare export data
        export_list = []
        for res in results:
            # Get the request to check has_error status
            request = res.request
            
            # Determine if result has error
            has_error = False
            if request:
                has_error = getattr(request, 'has_error', False) or request.status == RequestState.FAILED.value
            
            export_list.append({
                "request_id": str(res.original_request_id),  # Map back to original ID for Request Network
                "status": request.status if request else RequestState.COMPLETED.value,
                "has_error": has_error,
                "result_data": res.result_data,
            })
            
        # Write to JSONL string/bytes
        jsonl_content = ""
        for item in export_list:
            jsonl_content += json.dumps(item) + "\n"
        

        filename = f"results_{timestamp}.jsonl"
        meta_filename = f"results_{timestamp}.meta.json"
        
        file_bytes = jsonl_content.encode('utf-8')
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        
        metadata = {
            "batch_id": str(batch_id),
            "batch_type": "results",
            "filename": filename,
            "file_size": len(file_bytes),
            "record_count": len(results),
            "checksum": file_hash,
            "exported_at": datetime.utcnow().isoformat(),
            "version": 1
        }
        meta_bytes = json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8')
        
        export_type = export_config.get("storage_type", "local") # Use "storage_type" to match new config format
        
        # Fallback to "destination_type" if "storage_type" missing (key name changed in different versions)
        if "storage_type" not in export_config and "destination_type" in export_config:
            export_type = export_config["destination_type"]
            
        saved_path = ""

        if export_type == "local":
            local_path = Path(export_config.get("local_path", "/app/exports/results"))
            if not local_path.exists():
                local_path.mkdir(parents=True, exist_ok=True)

            # Save Data File (2-stage)
            file_path = local_path / filename
            tmp_file_path = local_path / f"{filename}.tmp"

            encrypted_bytes = encrypt_data(jsonl_content.encode('utf-8'))
            bio = io.BytesIO(encrypted_bytes)
            meta_bio = io.BytesIO(meta_bytes)
            
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
            # Upload files (2-stage)
            tmp_filename = f"{filename}.tmp"
            tmp_meta_filename = f"{meta_filename}.tmp"
            
            ftp.storbinary(f"STOR {tmp_filename}", bio)
            ftp.storbinary(f"STOR {tmp_meta_filename}", meta_bio)
            
            # Rename to final name
            try:
                ftp.delete(filename)
            except:
                pass
            ftp.rename(tmp_filename, filename)
            
            try:
                ftp.delete(meta_filename)
            except:
                pass
            ftp.rename(tmp_meta_filename, meta_filename)
            
            ftp.quit()
            saved_path = f"ftp://{host}/{remote_path}/{filename}"
            logger.info(f"Exported results to FTP: {saved_path}")

        # Mark as exported
        for res in results:
            res.exported_at = datetime.utcnow()
            res.export_batch_id = batch_id
            
        sync_history.status = "success"
        sync_history.details = {"exported_count": len(results), "method": export_type}
        sync_history.completed_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "status": "success",
            "count": len(results),
            "file": saved_path,
            "batch_id": str(batch_id)
        }
            
    except Exception as exc:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Result export failed: {exc}\n{error_trace}")
        db.rollback()
        try:
            sync_history.status = "failed"
            sync_history.details = {"error": str(exc), "traceback": error_trace}
            sync_history.completed_at = datetime.utcnow()
            db.commit()
        except:
            db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()