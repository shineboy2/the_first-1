"""
Celery task for sending file-based requests to FTP.
Called on-demand from execute_pending_queries when a file_request is detected.
"""
import logging
import tempfile
import os
from datetime import datetime

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings

logger = logging.getLogger(__name__)

# Sync database connection for Celery
sync_engine = create_engine(
    str(settings.DATABASE_URL).replace('postgresql+asyncpg', 'postgresql'),
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


@shared_task(bind=True, max_retries=3)
def send_file_request(self, file_request_id: str):
    """
    Generate a request file and upload it to FTP.

    Steps:
    1. Load FileRequest + FileRequestConfig from DB
    2. Load IncomingRequest for query_params
    3. Generate filename (FileRequestEngine.generate_filename)
    4. Generate file content (FileRequestEngine.generate_file_content)
    5. Get FTPStorageHandler from send_ftp_profile
    6. Upload file to send_path on FTP
    7. Update FileRequest status to "waiting_response"
    """
    from models.file_request import FileRequest
    from models.file_request_config import FileRequestConfig
    from models.incoming_request import IncomingRequest
    from services.file_request_engine import FileRequestEngine
    from services.ftp_profile_service import FTPProfileService

    db = SessionLocal()
    try:
        # 1. Load FileRequest
        file_req = db.query(FileRequest).filter(
            FileRequest.id == file_request_id
        ).first()

        if not file_req:
            logger.error(f"[FILE_REQUEST_SENDER] FileRequest {file_request_id} not found")
            return {"status": "error", "message": "FileRequest not found"}

        # 2. Load config and incoming request
        config = db.query(FileRequestConfig).filter(
            FileRequestConfig.id == file_req.file_request_config_id
        ).first()

        if not config:
            file_req.status = "failed"
            file_req.error_message = "FileRequestConfig not found"
            db.commit()
            return {"status": "error", "message": "Config not found"}

        incoming_req = db.query(IncomingRequest).filter(
            IncomingRequest.id == file_req.incoming_request_id
        ).first()

        if not incoming_req:
            file_req.status = "failed"
            file_req.error_message = "IncomingRequest not found"
            db.commit()
            return {"status": "error", "message": "IncomingRequest not found"}

        # 3. Build request data context
        request_data = dict(incoming_req.query_params or {})
        request_data["request_id"] = str(incoming_req.id)
        request_data["request_type"] = incoming_req.query_type or ""
        request_data["original_request_id"] = str(incoming_req.original_request_id)

        # 4. Generate filename
        filename = FileRequestEngine.generate_filename(config, request_data)
        file_req.filename = filename
        file_req.file_generated_at = datetime.utcnow()

        # 5. Generate file content
        content_bytes = FileRequestEngine.generate_file_content(config, request_data)
        file_req.file_content_hash = FileRequestEngine.compute_content_hash(content_bytes)

        # 6. Get FTP handler for sending
        ftp_handler = FTPProfileService.get_handler_sync(db, config.send_ftp_profile_id)
        if not ftp_handler:
            file_req.status = "failed"
            file_req.error_message = "Send FTP profile not found or inactive"
            db.commit()
            return {"status": "error", "message": "Send FTP profile not available"}

        # 7. Write content to temp file and upload
        file_req.status = "uploading"
        db.commit()

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(filename)[1] or ".json"
            ) as tmp:
                tmp.write(content_bytes)
                tmp_path = tmp.name

            # Upload to FTP at send_path/filename
            remote_path = f"{config.send_path.rstrip('/')}/{filename}"
            # FTPStorageHandler.upload_file is async, but we're in sync context
            # Use the underlying ftplib directly via the handler
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                upload_success = loop.run_until_complete(
                    ftp_handler.upload_file(tmp_path, remote_path)
                )
            finally:
                loop.close()

            if not upload_success:
                raise Exception("FTP upload returned False")

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        # 8. Update status
        file_req.status = "waiting_response"
        file_req.uploaded_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"[FILE_REQUEST_SENDER] Successfully uploaded {filename} "
            f"for request {incoming_req.id}"
        )

        return {
            "status": "success",
            "file_request_id": file_request_id,
            "filename": filename,
        }

    except Exception as e:
        logger.error(
            f"[FILE_REQUEST_SENDER] Error processing file request {file_request_id}: {e}",
            exc_info=True
        )
        db.rollback()

        # Try to update status
        try:
            file_req = db.query(FileRequest).filter(
                FileRequest.id == file_request_id
            ).first()
            if file_req:
                file_req.status = "failed"
                file_req.error_message = str(e)[:500]
                file_req.retry_count += 1

                # Also update incoming request
                incoming_req = db.query(IncomingRequest).filter(
                    IncomingRequest.id == file_req.incoming_request_id
                ).first()
                if incoming_req:
                    incoming_req.status = "failed"
                    incoming_req.last_error = f"File request send failed: {str(e)[:300]}"
                    incoming_req.has_error = True

                db.commit()
        except Exception:
            db.rollback()

        # Retry if possible
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=30 * (self.request.retries + 1))

        return {"status": "error", "message": str(e)}
    finally:
        db.close()
