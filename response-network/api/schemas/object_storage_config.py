"""
Pydantic schemas for Object Storage Configuration.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ObjectStorageConfigBase(BaseModel):
    """Base schema for Object Storage configuration."""
    name: str = Field(..., min_length=1, max_length=100, description="Unique identifier name")
    display_name: str = Field(..., min_length=1, max_length=200, description="Human-readable display name")
    description: Optional[str] = Field(None, max_length=500)
    storage_type: str = Field(default="minio", description="Storage type: minio, ceph, s3")
    endpoint_url: str = Field(..., description="S3-compatible endpoint URL")
    access_key: str = Field(..., description="Access Key ID")
    region: str = Field(default="us-east-1", description="Region name")
    default_bucket: str = Field(..., description="Default bucket name")
    use_ssl: bool = Field(default=False, description="Use SSL for connection")
    verify_ssl: bool = Field(default=False, description="Verify SSL certificate")
    path_style: bool = Field(default=True, description="Use path-style addressing (required for MinIO/Ceph)")
    timeout: int = Field(default=30, ge=5, le=300, description="Connection timeout in seconds")
    is_active: bool = Field(default=True, description="Whether this configuration is active")


class ObjectStorageConfigCreate(ObjectStorageConfigBase):
    """Schema for creating a new Object Storage configuration."""
    secret_key: str = Field(..., description="Secret Access Key (will be encrypted at rest)")


class ObjectStorageConfigUpdate(BaseModel):
    """Schema for updating an Object Storage configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    storage_type: Optional[str] = None
    endpoint_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = Field(None, description="New Secret Access Key (will be encrypted)")
    region: Optional[str] = None
    default_bucket: Optional[str] = None
    use_ssl: Optional[bool] = None
    verify_ssl: Optional[bool] = None
    path_style: Optional[bool] = None
    timeout: Optional[int] = Field(None, ge=5, le=300)
    is_active: Optional[bool] = None


class ObjectStorageConfigRead(ObjectStorageConfigBase):
    """Schema for reading Object Storage configuration (secret_key excluded)."""
    id: UUID
    last_tested_at: Optional[datetime] = None
    last_test_result: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
