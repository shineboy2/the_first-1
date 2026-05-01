from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, String, JSON, Boolean, Integer, Enum as SQLAEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from shared.database.base import Base
import enum

class WorkerType(enum.Enum):
    # Response network workers
    EXPORT_SETTINGS = "export_settings"
    EXPORT_RESULTS = "export_results"
    SYSTEM_MONITORING = "system_monitoring"
    
    # Request network workers (managed in response network, exported to request)
    IMPORT_SETTINGS = "import_settings"
    EXPORT_REQUESTS = "export_requests"
    IMPORT_RESULTS = "import_results"

class StorageType(enum.Enum):
    LOCAL = "local"
    FTP = "ftp"
    SFTP = "sftp"
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"

class WorkerSettings(Base):
    """Worker settings model for both networks. All settings are managed in response network."""
    __tablename__ = "worker_settings"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True)
    worker_type = Column(SQLAEnum(WorkerType), nullable=False, unique=True)
    
    # Storage settings
    storage_type = Column(SQLAEnum(StorageType), nullable=False)
    storage_path = Column(String, nullable=False)
    storage_config = Column(JSON, nullable=True)  # Additional storage-specific config
    
    # Schedule settings (only for response network workers)
    schedule_expression = Column(String, nullable=True)  # Crontab expression
    
    # Status
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    error_count = Column(Integer, default=0)
    last_error = Column(String, nullable=True)
    
    # Export tracking
    last_exported_at = Column(DateTime, nullable=True)  # When these settings were last exported
    
    # Metadata
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def update_next_run(self):
        """Update next_run based on schedule_expression."""
        if self.schedule_expression and self.is_response_network_worker():
            cron = croniter(self.schedule_expression, datetime.utcnow())
            self.next_run = cron.get_next(datetime)
    
    def is_response_network_worker(self) -> bool:
        """Check if this worker belongs to response network."""
        return self.worker_type in {
            WorkerType.EXPORT_SETTINGS,
            WorkerType.EXPORT_RESULTS,
            WorkerType.SYSTEM_MONITORING
        }
    
    def is_request_network_worker(self) -> bool:
        """Check if this worker belongs to request network."""
        return self.worker_type in {
            WorkerType.IMPORT_SETTINGS,
            WorkerType.EXPORT_REQUESTS,
            WorkerType.IMPORT_RESULTS
        }