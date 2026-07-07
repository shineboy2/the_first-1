"""
Celery task for polling FTP servers for file-based request responses.
Runs periodically (every 60 seconds by default) to check for response files.
"""
import asyncio
import logging
import tempfile
import os
import uuid
from datetime import datetime, timedelta

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.config import settings

from models.file_request import FileRequest
from models.file_request_config import FileRequestConfig
from models.incoming_request import IncomingRequest
from models.query_result import QueryResult
from services.file_request_engine import FileRequestEngine
from services.ftp_profile_service import FTPProfileService

logger = logging.getLogger(__name__)

# Sync database connection for Celery
sync_engine = create_engine(
    str(settings.DATABASE_URL).replace('postgresql+asyncpg', 'postgresql'),
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


@shared_task(bind=True, max_retries=3)
def poll_file_responses(self):
    """
    Poll FTP servers for response files matching pending file requests.

    Steps:
    1. Query all FileRequests with status "waiting_response"
    2. Group by receive_ftp_profile to minimize FTP connections
    3. For each group: connect to FTP, list files in receive_path
    4. For each pending request: check if response file exists
    5. If found: download, parse, store result, mark complete
    6. If not found: check timeout, update poll count
    """
    db = SessionLocal()
    try:
        # 1. Get all waiting file requests
        waiting_requests = db.query(FileRequest).filter(
            FileRequest.status == "waiting_response"
        ).all()

        if not waiting_requests:
            return {"status": "no_waiting_requests"}

        logger.info(
            f"[FILE_POLLER] Found {len(waiting_requests)} waiting file requests"
        )

        # 2. Group by config's receive_ftp_profile_id
        grouped = {}
        for freq in waiting_requests:
            config = db.query(FileRequestConfig).filter(
                FileRequestConfig.id == freq.file_request_config_id
            ).first()
            if not config:
                freq.status = "failed"
                freq.error_message = "FileRequestConfig not found"
                continue

            key = (config.receive_ftp_profile_id, config.receive_path)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append((freq, config))

        processed = 0
        completed = 0
        timed_out = 0

        # 3. Process each FTP group
        for (profile_id, receive_path), items in grouped.items():
            ftp_handler = FTPProfileService.get_handler_sync(db, profile_id)
            if not ftp_handler:
                for freq, _ in items:
                    freq.error_message = "Receive FTP profile not available"
                    freq.last_poll_at = datetime.utcnow()
                    freq.poll_count += 1
                db.commit()
                continue

            # List files on FTP at receive_path
            try:
                loop = asyncio.new_event_loop()
                try:
                    remote_files = loop.run_until_complete(
                        ftp_handler.list_files(receive_path.lstrip("/"))
                    )
                finally:
                    loop.close()

                # Extract just filenames (list_files returns paths)
                remote_filenames = set()
                for f in remote_files:
                    # list_files returns relative paths, extract basename
                    remote_filenames.add(os.path.basename(f))

            except Exception as e:
                logger.error(
                    f"[FILE_POLLER] Failed to list FTP files at "
                    f"profile={profile_id}, path={receive_path}: {e}"
                )
                for freq, _ in items:
                    freq.last_poll_at = datetime.utcnow()
                    freq.poll_count += 1
                db.commit()
                continue

            # 4. Check each pending request
            for freq, config in items:
                processed += 1
                now = datetime.utcnow()
                freq.last_poll_at = now
                freq.poll_count += 1

                # Look for response file with the same filename
                response_filename = freq.filename
                if not response_filename:
                    freq.error_message = "No filename set on FileRequest"
                    continue

                if response_filename in remote_filenames:
                    # 5. Response found — download and parse
                    logger.info(
                        f"[FILE_POLLER] Response found: {response_filename} "
                        f"for request {freq.incoming_request_id}"
                    )
                    freq.status = "response_received"
                    freq.response_detected_at = now
                    freq.response_filename = response_filename

                    try:
                        # Download file
                        tmp_path = None
                        try:
                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=".json"
                            ) as tmp:
                                tmp_path = tmp.name

                            remote_file_path = f"{receive_path.rstrip('/')}/{response_filename}"

                            loop = asyncio.new_event_loop()
                            try:
                                download_ok = loop.run_until_complete(
                                    ftp_handler.download_file(
                                        remote_file_path.lstrip("/"), tmp_path
                                    )
                                )
                            finally:
                                loop.close()

                            if not download_ok:
                                raise Exception("FTP download returned False")

                            freq.response_downloaded_at = datetime.utcnow()

                            # Read content
                            with open(tmp_path, "rb") as f:
                                raw_content = f.read()

                        finally:
                            if tmp_path and os.path.exists(tmp_path):
                                os.unlink(tmp_path)

                        # Store raw content
                        freq.response_raw_content = raw_content.decode(
                            "utf-8", errors="replace"
                        )

                        # Parse response
                        freq.status = "parsing"
                        parser_config = config.response_parser_config or {}
                        parse_result = FileRequestEngine.parse_response(
                            parser_config, raw_content
                        )

                        freq.parsed_result = parse_result.get("data")
                        freq.parsed_at = datetime.utcnow()

                        # Load incoming request
                        incoming_req = db.query(IncomingRequest).filter(
                            IncomingRequest.id == freq.incoming_request_id
                        ).first()

                        if parse_result["success"]:
                            # Create/update QueryResult
                            result_data = {
                                "file_response": parse_result["data"],
                                "parse_success": True,
                            }

                            existing_qr = db.query(QueryResult).filter(
                                QueryResult.request_id == freq.incoming_request_id
                            ).first()

                            if existing_qr:
                                existing_qr.result_data = result_data
                                existing_qr.result_count = (
                                    len(parse_result["data"])
                                    if isinstance(parse_result["data"], list)
                                    else 1
                                )
                                existing_qr.execution_time_ms = 0
                                existing_qr.elasticsearch_took_ms = 0
                                existing_qr.executed_at = datetime.utcnow()
                                existing_qr.cache_hit = False
                            else:
                                new_qr = QueryResult(
                                    id=uuid.uuid4(),
                                    request_id=freq.incoming_request_id,
                                    original_request_id=incoming_req.original_request_id,
                                    result_data=result_data,
                                    result_count=(
                                        len(parse_result["data"])
                                        if isinstance(parse_result["data"], list)
                                        else 1
                                    ),
                                    execution_time_ms=0,
                                    elasticsearch_took_ms=0,
                                    cache_hit=False,
                                    executed_at=datetime.utcnow(),
                                )
                                db.add(new_qr)

                            # Mark as completed
                            freq.status = "completed"
                            if incoming_req:
                                incoming_req.status = "completed"
                                incoming_req.completed_at = datetime.utcnow()
                                incoming_req.progress = 100.0
                                incoming_req.has_error = False

                            completed += 1
                        else:
                            # Parse failed or error detected in response
                            error_msg = parse_result.get("error", "Unknown parse error")
                            freq.status = "failed"
                            freq.error_message = error_msg

                            if incoming_req:
                                incoming_req.status = "failed"
                                incoming_req.completed_at = datetime.utcnow()
                                incoming_req.error_message = (
                                    f"File response parse error: {error_msg[:300]}"
                                )
                                incoming_req.has_error = True

                    except Exception as e:
                        logger.error(
                            f"[FILE_POLLER] Error processing response "
                            f"{response_filename}: {e}",
                            exc_info=True,
                        )
                        freq.status = "failed"
                        freq.error_message = f"Response processing error: {str(e)[:400]}"

                else:
                    # 6. Response not found — check timeout
                    if freq.uploaded_at:
                        elapsed = now - freq.uploaded_at
                        timeout_td = timedelta(
                            minutes=config.response_timeout_minutes
                        )

                        if elapsed > timeout_td:
                            # Timeout!
                            freq.status = "timeout"
                            freq.error_message = (
                                f"Response timeout after {config.response_timeout_minutes} minutes"
                            )
                            timed_out += 1

                            incoming_req = db.query(IncomingRequest).filter(
                                IncomingRequest.id == freq.incoming_request_id
                            ).first()
                            if incoming_req:
                                incoming_req.status = "failed"
                                incoming_req.completed_at = datetime.utcnow()
                                incoming_req.error_message = "File request response timeout"
                                incoming_req.has_error = True

            db.commit()

        return {
            "status": "success",
            "processed": processed,
            "completed": completed,
            "timed_out": timed_out,
        }

    except Exception as e:
        logger.error(f"[FILE_POLLER] Unexpected error: {e}", exc_info=True)
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
