from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
import uuid


class UserBase(BaseModel):
    """Shared properties for a user."""
    email: str
    username: str
    full_name: Optional[str] = None  # Using Optional explicitly
    daily_request_limit: int = 100
    monthly_request_limit: int = 2000
    max_results_per_request: int = 1000
    allowed_indices: list[str] = []
    allowed_external_apis: list[str] = []


class UserRead(UserBase):
    """Properties to return to a client."""
    id: uuid.UUID
    profile_type: str
    is_active: bool
    daily_request_limit: int
    monthly_request_limit: int
    max_results_per_request: int
    allowed_indices: list[str]
    allowed_external_apis: list[str]

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    """Properties to receive via API on creation."""
    password: str
    profile_type: str = "user"
    is_active: bool = True
    is_admin: bool = False

    @field_validator('profile_type')
    @classmethod
    def validate_profile_type(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('profile_type must be a non-empty string')
        return v


class UserUpdate(BaseModel):
    """Properties that can be updated."""
    email: str | None = None
    full_name: str | None = None
    username: str | None = None
    password: str | None = None
    profile_type: str | None = None
    allowed_external_apis: list[str] | None = None

    @field_validator('profile_type')
    @classmethod
    def validate_profile_type(cls, v):
        if v is not None and not v:
            raise ValueError('profile_type must be a non-empty string')
        return v


class ChangePasswordRequest(BaseModel):
    """Request to change own password (user)"""
    current_password: str
    new_password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldPassword123",
                "new_password": "newPassword456"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Request to reset user password (admin)"""
    new_password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_password": "tempPassword123"
            }
        }


class PasswordChangeResponse(BaseModel):
    """Response after password change"""
    message: str
    username: str
    success: bool


class UserStats(BaseModel):
    """User statistics."""
    total_requests: int
    completed_requests: int
    failed_requests: int
    avg_processing_time: float
    requests_today: int
    requests_this_month: int


class UserWithStats(UserRead):
    """User with statistics."""
    stats: UserStats

    class Config:
        from_attributes = True