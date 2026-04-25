import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from shared.database.base import BaseModel, UUIDMixin

class Response(UUIDMixin, BaseModel):
    """
    Represents the result of a processed request.
    """
    __tablename__ = "responses"

    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    result_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    is_cached: Mapped[bool] = mapped_column(Boolean, default=False)
    cache_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    has_error: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationship back to the request
    request: Mapped["Request"] = relationship("Request", back_populates="response")