import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import BaseModel
from shared.database.base import UUIDMixin

class SyncHistory(BaseModel, UUIDMixin):
    __tablename__ = "sync_history"
    
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # e.g. "success", "failed", "in_progress"
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True) # JSON object with error trace or files count
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
