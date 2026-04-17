from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class UserRequestAccessBase(BaseModel):
    max_requests_per_hour: int = Field(100, ge=1)
    is_active: bool = True


class UserRequestAccessCreate(UserRequestAccessBase):
    user_id: UUID
    request_type_id: UUID


class UserRequestAccessInput(UserRequestAccessBase):
    request_type_id: UUID


class BulkUserRequestAccessCreate(BaseModel):
    user_ids: List[UUID]
    max_requests_per_hour: int = Field(100, ge=1)
    is_active: bool = True


class UserRequestAccessUpdate(BaseModel):
    max_requests_per_hour: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class UserBriefRead(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: Optional[str] = None
    profile_type: str

    class Config:
        from_attributes = True


class UserRequestAccessRead(UserRequestAccessBase):
    id: UUID
    user_id: UUID
    request_type_id: UUID
    created_at: datetime
    updated_at: datetime
    user: Optional[UserBriefRead] = None

    class Config:
        from_attributes = True


class UserRequestAccessReadSimple(UserRequestAccessBase):
    """Simple read schema without nested relationships for async context compatibility"""
    id: UUID
    user_id: UUID
    request_type_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True