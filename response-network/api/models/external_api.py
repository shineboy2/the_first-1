from typing import Optional
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import BaseModel, UUIDMixin, TimestampMixin


class ExternalAPI(BaseModel, UUIDMixin, TimestampMixin):
    __tablename__ = "external_apis"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    endpoint_url: Mapped[str] = mapped_column(String(500), nullable=False)
    http_method: Mapped[str] = mapped_column(String(20), nullable=False, default="POST")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Authentication Configuration
    # Options: 'none', 'static_key', 'dynamic_token'
    auth_type: Mapped[str] = mapped_column(String(50), nullable=False, default="none")
    
    # JSON containing specific auth info dependent on auth_type
    # Example for dynamic_token: {"auth_url": "...", "auth_payload": {...}, "token_path": "data.access_token"}
    auth_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Static headers to send with the actual request (e.g., Content-Type, API keys if static_key)
    static_headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Template for the request payload. E.g., {"image": "{{file_data}}"}
    payload_template: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self):
        return f"<ExternalAPI(name={self.name}, auth_type={self.auth_type})>"
