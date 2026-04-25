import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Column, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from shared.database.base import BaseModel, TimestampMixin


class IncomingRequest(BaseModel, TimestampMixin):
    __tablename__ = "incoming_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # The ID from the Request Network
    original_request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True, unique=True)
    # No foreign key, it's an isolated network
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    query_type: Mapped[str] = mapped_column(String(50), nullable=False)
    query_params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    elasticsearch_query: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='pending', index=True)
    assigned_worker: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_error: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    result = relationship("QueryResult", back_populates="request", uselist=False, cascade="all, delete-orphan", lazy="joined")