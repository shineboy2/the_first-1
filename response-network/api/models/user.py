import typing
from typing import List
import uuid
import sys
import datetime
from pathlib import Path

# Ensure Response Network API is in sys.path
_api_dir = Path(__file__).resolve().parent.parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

from sqlalchemy import (
    Boolean,
    String,
    TIMESTAMP,
    UUID,
    Integer,
    ARRAY,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from shared.database.base import Base, TimestampMixin
from core.hashing import verify_password

if typing.TYPE_CHECKING:
    from models.settings import UserSettings  # Import only for type hints

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    __tablename__ = "users"

# id is inherited from UUIDMixin
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    settings: Mapped[list["UserSettings"]] = relationship("UserSettings", back_populates="user", cascade="all, delete-orphan")
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Adding required fields from schema
    daily_request_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    monthly_request_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
    max_results_per_request: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    allowed_indices: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    allowed_external_apis: Mapped[List[str]] = mapped_column(JSONB, nullable=False, server_default='[]')
    profile_type: Mapped[str] = mapped_column(String(50), ForeignKey("profile_type_configs.name"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Security Fields (Phase 2)
    force_password_change: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')
    allowed_ips: Mapped[list] = mapped_column(JSONB, nullable=False, server_default='[]')
    password_changed_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationships
    requests: Mapped[list["Request"]] = relationship("Request", back_populates="user", cascade="all, delete-orphan")
    created_request_types: Mapped[list["RequestType"]] = relationship("RequestType", back_populates="created_by")
    request_access: Mapped[list["UserRequestAccess"]] = relationship("UserRequestAccess", back_populates="user")

    def verify_password(self, password: str) -> bool:
        """Verifies the provided password against the stored hash."""
        return verify_password(password, self.hashed_password)