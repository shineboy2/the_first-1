from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from shared.database.base import Base

class FileImportState(Base):
    __tablename__ = "file_import_state"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    resource_type = Column(String, index=True, nullable=False)
    status = Column(String, default="PROCESSING", index=True, nullable=False) # PROCESSING, PROCESSED, FAILED
    worker_id = Column(String, nullable=True)
    lease_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
