import uuid
from sqlalchemy import Boolean, Integer, String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import bcrypt

from shared.database.base import BaseModel


class User(BaseModel):
    """
    Represents a read-only replica of a user in the Request Network.
    This data is synced from the Response Network and is used primarily
    for rate limiting and associating requests with a user profile.
    """
    __tablename__ = "users"

    # The ID is the primary key but is not auto-generated like in BaseModel.
    # It's synced from the source of truth in the Response Network.
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    profile_type: Mapped[str] = mapped_column(String(50), nullable=False, default='basic', index=True)
    
    # Request Type Access Control
    allowed_request_types: Mapped[list] = mapped_column(JSONB, nullable=False, server_default='[]')
    blocked_request_types: Mapped[list] = mapped_column(JSONB, nullable=False, server_default='[]')
    allowed_external_apis: Mapped[list] = mapped_column(JSONB, nullable=False, server_default='[]')
    
    # Rate Limits
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    rate_limit_per_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    rate_limit_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    
    # Daily/Monthly Limits
    daily_request_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    monthly_request_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)

    # SubUser Rate Limits
    subuser_rate_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=10, server_default='10')
    subuser_rate_limit_per_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default='100')
    subuser_rate_limit_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=500, server_default='500')
    
    max_subusers: Mapped[int] = mapped_column(Integer, nullable=False, default=10, server_default='10')

    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    synced_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Security Fields (Phase 1)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    locked_until: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_login_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    force_password_change: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')
    allowed_ips: Mapped[list] = mapped_column(JSONB, nullable=False, server_default='[]')
    password_changed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship to requests
    requests: Mapped[list["Request"]] = relationship("Request", back_populates="user", cascade="all, delete-orphan")

    def is_request_type_allowed(self, request_type: str) -> bool:
        """
        Check if user is allowed to submit this request type.
        
        Priority:
        1. If admin -> True
        2. If in blocked_request_types → False
        3. If allowed_request_types is empty → False (allow NONE, Secure Default)
        4. If allowed_request_types is not empty → must be in it
        """
        if self.profile_type == 'admin':
            return True

        if request_type in self.blocked_request_types:
            return False
        
        if not self.allowed_request_types:  # Empty list = allow NONE (Secure Default)
            return False
        
        return request_type in self.allowed_request_types

    def is_external_api_allowed(self, api_name: str) -> bool:
        """
        Check if user is allowed to submit this external API type.
        """
        return api_name in self.allowed_external_apis

    def verify_password(self, password: str) -> bool:
        """
        Verifies a given password against the stored hash.
        """
        if not password or not self.hashed_password:
            return False

        password_bytes = password.encode('utf-8')
        hashed_password_bytes = self.hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_password_bytes)

    def __repr__(self):
        return f"<UserReplica(id={self.id}, username='{self.username}')>"