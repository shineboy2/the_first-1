from datetime import datetime
from uuid import UUID
from typing import List

from pydantic import BaseModel, Field

from schemas.base import CamelModel


class SettingsBase(CamelModel):
    """Base settings schema."""
    key: str
    value: dict
    description: str | None = None
    is_active: bool = True
    

class SettingsCreate(SettingsBase):
    """Schema for creating settings."""
    pass


class SettingsUpdate(SettingsBase):
    """Schema for updating settings."""
    key: str | None = None
    value: dict | None = None
    description: str | None = None
    is_active: bool | None = None


class Settings(SettingsBase):
    """Schema for reading settings."""
    id: str | None | UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SettingsImport(BaseModel):
    """Schema for settings import file."""
    settings: List[Settings]
    exported_at: datetime = Field(description="UTC timestamp of when export was created")
    version: int = Field(default=1, description="Export format version")