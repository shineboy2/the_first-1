"""
Pydantic schemas for FTP Profile.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FTPProfileCreate(BaseModel):
    """Schema for creating a new FTP profile."""
    name: str = Field(..., min_length=1, max_length=100, description="Unique identifier name")
    display_name: str = Field(..., min_length=1, max_length=200, description="Human-readable display name")
    description: Optional[str] = Field(None, max_length=500)
    host: str = Field(..., min_length=1, max_length=255, description="FTP server hostname or IP")
    port: int = Field(21, ge=1, le=65535, description="FTP server port")
    username: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, max_length=255)
    base_path: str = Field("/", max_length=500, description="Base directory path on FTP server")
    use_tls: bool = Field(False, description="Use FTP over TLS (FTPS)")
    passive_mode: bool = Field(True, description="Use passive mode for data connections")
    timeout: int = Field(30, ge=5, le=300, description="Connection timeout in seconds")
    is_active: bool = True


class FTPProfileUpdate(BaseModel):
    """Schema for updating an FTP profile. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, max_length=255)
    base_path: Optional[str] = Field(None, max_length=500)
    use_tls: Optional[bool] = None
    passive_mode: Optional[bool] = None
    timeout: Optional[int] = Field(None, ge=5, le=300)
    is_active: Optional[bool] = None


class FTPProfileRead(BaseModel):
    """Schema for reading FTP profile — password excluded for security."""
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    host: str
    port: int
    username: Optional[str]
    base_path: str
    use_tls: bool
    passive_mode: bool
    timeout: int
    is_active: bool
    last_tested_at: Optional[datetime]
    last_test_result: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FTPProfileTestResult(BaseModel):
    """Result of an FTP connection test."""
    success: bool
    message: str
    can_read: bool = False
    can_write: bool = False
    tested_at: datetime
