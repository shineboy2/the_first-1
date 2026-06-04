import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import BaseModel, UUIDMixin, TimestampMixin

class ApiKey(BaseModel, UUIDMixin, TimestampMixin):
    """
    Represents API keys for service-to-service authentication.
    """
    __tablename__ = "api_keys"

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    scopes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)