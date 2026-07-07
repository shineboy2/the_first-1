"""
Cleanup Task for Response Network
Automatically cleans up old export/import files
"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from celery import shared_task
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker
import json

from models.sync_history import SyncHistory
from models.query_result import QueryResult
import sys
import os

logger = logging.getLogger(__name__)


@shared_task(name="cleanup.cleanup_old_files")
def cleanup_old_files():
    """
    پاکسازی فایل‌های قدیمی export و import
    - فایل‌های export قدیمی‌تر از 7 روز
    - فایل‌های import آرشیو شده قدیمی‌تر از 30 روز
    """
    try:
        logger.info("Starting cleanup task for old files...")
        
        # تنظیمات
        export_retention_days = 7
        import_retention_days = 30
        
        # مسیرهای فایل
        base_dir = Path("/app")
        export_dir = base_dir / "exports"
        import_archive_dir = base_dir / "imports" / "archive"
        
        stats = {
            "exports_deleted": 0,
            "imports_deleted": 0,
            "total_size_freed": 0,
            "sync_history_deleted": 0,
            "base64_results_cleaned": 0
        }
        
        # پاکسازی تاریخچه همگام‌سازی از دیتابیس (قدیمی‌تر از 30 روز) و base64های دیتابیس
        try:
            db_user = os.getenv("RESPONSE_DB_USER", "postgres")
            db_pass = os.getenv("RESPONSE_DB_PASSWORD", "postgres")
            db_host = os.getenv("RESPONSE_DB_HOST", "127.0.0.1")
            db_port = os.getenv("RESPONSE_DB_PORT", "5432")
            db_name = os.getenv("RESPONSE_DB_NAME", "response_network")
            database_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            
            engine = create_engine(database_url)
            SessionLocal = sessionmaker(bind=engine)
            
            with SessionLocal() as session:
                cutoff_db_date = datetime.utcnow() - timedelta(days=30)
                result = session.execute(
                    delete(SyncHistory).where(SyncHistory.started_at < cutoff_db_date)
                )
                stats["sync_history_deleted"] = result.rowcount
                session.commit()
                logger.info(f"Cleaned {stats['sync_history_deleted']} old SyncHistory records (>{30} days)")
                
                # پاکسازی دیتای سنگین Base64 از نتایج کوئری قدیمی‌تر از 7 روز
                cutoff_db_date_results = datetime.utcnow() - timedelta(days=7)
                # We need to find QueryResults that have result_data -> api_response -> similar_faces
                # Note: For SQLite/Postgres compatibility we fetch them and update
                old_results = session.query(QueryResult).filter(
                    QueryResult.executed_at < cutoff_db_date_results
                ).all()
                
                cleaned_count = 0
                for result_obj in old_results:
                    if not result_obj.result_data:
                        continue
                    
                    data = result_obj.result_data
                    # Check if it has face recognition structure
                    api_resp = data.get("api_response", {})
                    if api_resp and "similar_faces" in api_resp:
                        faces = api_resp.get("similar_faces", [])
                        changed = False
                        for face in faces:
                            if face.get("source_photo_b64") and not face["source_photo_b64"].startswith("["):
                                face["source_photo_b64"] = "[CLEANED_UP_AFTER_7_DAYS]"
                                changed = True
                            if face.get("thumbnail_b64") and not face["thumbnail_b64"].startswith("["):
                                face["thumbnail_b64"] = "[CLEANED_UP_AFTER_7_DAYS]"
                                changed = True
                        
                        if changed:
                            # Modify dict inplace won't always trigger SQLAlchemy update for JSON, 
                            # we need to reassign or use flag_modified
                            result_obj.result_data = dict(data)
                            cleaned_count += 1
                
                if cleaned_count > 0:
                    stats["base64_results_cleaned"] = cleaned_count
                    session.commit()
                    logger.info(f"Cleaned base64 images from {cleaned_count} old QueryResults (>{7} days)")
                    
        except Exception as e:
            logger.error(f"Failed to clean SyncHistory: {e}")
        
        # پاکسازی فایل‌های export قدیمی
        if export_dir.exists():
            cutoff_date = datetime.now() - timedelta(days=export_retention_days)
            stats["exports_deleted"], size_freed = _cleanup_directory(
                export_dir, cutoff_date, "*.jsonl"
            )
            stats["total_size_freed"] += size_freed
            logger.info(f"Cleaned {stats['exports_deleted']} old export files (>{export_retention_days} days)")
        
        # پاکسازی فایل‌های import آرشیو شده قدیمی
        if import_archive_dir.exists():
            cutoff_date = datetime.now() - timedelta(days=import_retention_days)
            stats["imports_deleted"], size_freed = _cleanup_directory(
                import_archive_dir, cutoff_date, "*.jsonl"
            )
            stats["total_size_freed"] += size_freed
            logger.info(f"Cleaned {stats['imports_deleted']} old import archive files (>{import_retention_days} days)")
        
        # گزارش نهایی
        size_mb = stats["total_size_freed"] / (1024 * 1024)
        logger.info(
            f"Cleanup completed: {stats['exports_deleted'] + stats['imports_deleted']} files deleted, "
            f"{size_mb:.2f} MB freed"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}", exc_info=True)
        raise


def _cleanup_directory(directory: Path, cutoff_date: datetime, pattern: str = "*"):
    """
    پاکسازی فایل‌های قدیمی در یک دایرکتوری
    
    Args:
        directory: مسیر دایرکتوری
        cutoff_date: تاریخ حد (فایل‌های قدیمی‌تر از این حذف می‌شوند)
        pattern: الگوی فایل‌ها (مثلاً *.jsonl)
    
    Returns:
        tuple: (تعداد فایل‌های حذف شده, حجم آزاد شده به بایت)
    """
    deleted_count = 0
    size_freed = 0
    
    try:
        for file_path in directory.glob(pattern):
            if not file_path.is_file():
                continue
            
            # بررسی تاریخ فایل
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            if file_mtime < cutoff_date:
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    size_freed += file_size
                    logger.debug(f"Deleted old file: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")
    
    except Exception as e:
        logger.error(f"Error cleaning directory {directory}: {e}")
    
    return deleted_count, size_freed
