"""
Model for storing user profile types with their configurations
"""

import uuid
from typing import List
from sqlalchemy import String, Boolean, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY

from shared.database.base import Base, TimestampMixin


class ProfileTypeConfig(Base, TimestampMixin):
    """
    Configuration for user profile types.
    Allows admins to define and manage different user profiles.
    """
    __tablename__ = "profile_type_configs"

    # Basic info
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Permissions and limits
    permissions: Mapped[dict] = mapped_column(
        JSON, 
        nullable=False, 
        default=lambda: {
            "allowed_request_types": [],
            "blocked_request_types": [],
            "allowed_external_apis": [],
            "max_results_per_request": 1000
        }
    )
    daily_request_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    monthly_request_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
    
    # Rate limits
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    rate_limit_per_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    
    # Status and metadata
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    config_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    def __repr__(self):
        return f"<ProfileTypeConfig(name={self.name}, display_name={self.display_name})>"
    
    def get_allowed_request_types(self) -> list:
        """Get list of allowed request types for this profile"""
        return self.permissions.get("allowed_request_types", [])
    
    def get_blocked_request_types(self) -> list:
        """Get list of blocked request types for this profile"""
        return self.permissions.get("blocked_request_types", [])
    
    def is_request_type_allowed(self, request_type: str) -> bool:
        """Check if a specific request type is allowed for this profile"""
        allowed = self.get_allowed_request_types()
        blocked = self.get_blocked_request_types()
        
        # اگر allowed list خالی باشد، همه مجاز است (مگر blocked باشند)
        if not allowed:
            return request_type not in blocked
        
        # اگر allowed list پُر باشد، فقط آن‌ها مجاز هستند
        return request_type in allowed and request_type not in blocked

    def get_allowed_external_apis(self) -> list:
        """Get list of allowed external APIs for this profile"""
        return self.permissions.get("allowed_external_apis", [])
    
    def is_external_api_allowed(self, api_name: str) -> bool:
        """Check if a specific external API is allowed for this profile"""
        allowed = self.get_allowed_external_apis()
        # For simplicity, if allowed list is empty, we default to False for external APIs
        # unless we want the same logic as request types (Default allow all if empty).
        # We will use the explicit allow list approach for external APIs for security.
        return api_name in allowed

    # Relationships
    request_access: Mapped[List["ProfileTypeRequestAccess"]] = relationship("ProfileTypeRequestAccess", back_populates="profile_type")
