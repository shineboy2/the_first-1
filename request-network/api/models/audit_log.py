import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Column, ForeignKey, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import BaseModel

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    # Override id to be BigInteger
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Sync fields for Exporting to Response Network
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    export_batch_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)