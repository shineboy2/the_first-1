import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .constants import RequestState

from shared.database.base import BaseModel, TimestampMixin

class Request(BaseModel, TimestampMixin):
    """
    Represents a user's request submitted to the system.
    """
    __tablename__ = "requests"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sub_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sub_users.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    query_type: Mapped[str] = mapped_column(String(50), nullable=False)
    query_params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    elasticsearch_query: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=RequestState.PENDING.value, index=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    export_batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    result_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # State Machine Fields
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="requests")
    sub_user: Mapped["SubUser"] = relationship("SubUser")
    response: Mapped["Response"] = relationship("Response", back_populates="request", uselist=False, cascade="all, delete-orphan")

    @property
    def error_message(self) -> str | None:
        return self.last_error

    @error_message.setter
    def error_message(self, value: str | None) -> None:
        self.last_error = value

    @property
    def retry_count(self) -> int:
        return self.attempt_count

    @retry_count.setter
    def retry_count(self, value: int) -> None:
        self.attempt_count = value

    def __repr__(self):
        return f"<Request(id={self.id}, user_id={self.user_id}, status='{self.status}')>"