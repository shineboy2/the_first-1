"""
Schemas for profile type configuration management
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ProfileTypeConfigBase(BaseModel):
    """Base schema for profile type configuration"""
    display_name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    permissions: dict = Field(default_factory=dict)
    daily_request_limit: int = Field(default=100, ge=1)
    monthly_request_limit: int = Field(default=2000, ge=1)
    max_results_per_request: int = Field(default=1000, ge=1)
    is_active: bool = True
    config_metadata: Optional[dict] = None


class ProfileTypeConfigCreate(ProfileTypeConfigBase):
    """Schema for creating a profile type"""
    name: str = Field(..., min_length=1, max_length=50, pattern="^[a-zA-Z0-9_-]+$")


class ProfileTypeConfigUpdate(BaseModel):
    """Schema for updating a profile type"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, pattern="^[a-z_]+$")
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    permissions: Optional[dict] = None
    daily_request_limit: Optional[int] = Field(None, ge=1)
    monthly_request_limit: Optional[int] = Field(None, ge=1)
    max_results_per_request: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    config_metadata: Optional[dict] = None


class ProfileTypeConfigRead(ProfileTypeConfigBase):
    """Schema for reading profile type configuration"""
    name: str
    is_builtin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AvailablePermission(BaseModel):
    """Available permission for profile types"""
    name: str
    description: str


class ProfileTypeStatsRead(BaseModel):
    """Statistics about profile type usage"""
    profile_type: str
    user_count: int
    active_users: int
