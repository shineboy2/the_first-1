from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None


class User(UserBase):
    id: UUID | str
    profile_type: str
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    rate_limit_per_day: int
    daily_request_limit: int = 100
    monthly_request_limit: int = 2000
    priority: int
    is_active: bool
    allowed_indices: Optional[list[str]] = None
    allowed_request_types: Optional[list] = []
    blocked_request_types: Optional[list] = []
    allowed_external_apis: Optional[list] = []
    
    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: str


class ChangePasswordRequest(BaseModel):
    """User request to change own password"""
    current_password: str
    new_password: str


class PasswordChangeResponse(BaseModel):
    """Response after password change"""
    success: bool
    message: str
    username: str