from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import BaseModel, UUIDMixin, TimestampMixin


class ElasticsearchConfig(BaseModel, UUIDMixin, TimestampMixin):
    """Elasticsearch configuration model for runtime settings."""
    __tablename__ = "elasticsearch_config"

    url: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verify_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    def to_read(self):
        """Convert to read schema (without password)."""
        from schemas.elasticsearch_config import ElasticsearchConfigRead
        return ElasticsearchConfigRead(
            id=self.id,
            url=self.url,
            username=self.username,
            verify_ssl=self.verify_ssl,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
