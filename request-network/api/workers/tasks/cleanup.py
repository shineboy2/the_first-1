"""
Cleanup Task for Request Network
Automatically cleans up old export/import files
"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from celery import shared_task

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
            "total_size_freed": 0
        }
        
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
        
        # پاکسازی Audit Logs قدیمی که سینک شده‌اند (7 روز)
        stats["synced_logs_deleted"] = _cleanup_synced_audit_logs(export_retention_days)
        
        # گزارش نهایی
        size_mb = stats["total_size_freed"] / (1024 * 1024)
        logger.info(
            f"Cleanup completed: {stats['exports_deleted'] + stats['imports_deleted']} files deleted, "
            f"{stats['synced_logs_deleted']} synced audit logs deleted, "
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
                    logger.error(f"Failed to delete {file_path}: {e}")
                    
    except Exception as e:
        logger.error(f"Error accessing directory {directory}: {e}")
        
    return deleted_count, size_freed


def _cleanup_synced_audit_logs(retention_days: int) -> int:
    """
    Delete synced audit logs older than retention_days from the database.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from core.config import settings
    from models.audit_log import AuditLog
    
    deleted_count = 0
    
    try:
        # Setup sync database connection
        sync_engine = create_engine(
            str(settings.DATABASE_URL).replace('postgresql+asyncpg', 'postgresql+psycopg'),
            pool_pre_ping=True
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
        
        db = SessionLocal()
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Find logs that are "synced" and older than cutoff_date
            logs_to_delete = db.query(AuditLog).filter(
                AuditLog.sync_status == "synced",
                AuditLog.created_at < cutoff_date
            ).all()
            
            for log in logs_to_delete:
                db.delete(log)
                deleted_count += 1
                
            db.commit()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error cleaning up synced audit logs: {e}")
        
    return deleted_count
