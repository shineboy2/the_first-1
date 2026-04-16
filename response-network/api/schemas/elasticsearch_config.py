from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ElasticsearchConfigBase(BaseModel):
    """Base schema for Elasticsearch configuration."""
    url: str = Field(..., description="Elasticsearch URL (e.g., http://localhost:9200)")
    username: Optional[str] = Field(None, description="Username for Elasticsearch authentication")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificate")
    is_active: bool = Field(default=True, description="Whether this configuration is active")


class ElasticsearchConfigCreate(ElasticsearchConfigBase):
    """Schema for creating Elasticsearch configuration."""
    password: Optional[str] = Field(None, description="Password for Elasticsearch authentication")


class ElasticsearchConfigUpdate(BaseModel):
    """Schema for updating Elasticsearch configuration."""
    url: Optional[str] = Field(None, description="Elasticsearch URL")
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    verify_ssl: Optional[bool] = Field(None, description="Verify SSL certificate")
    is_active: Optional[bool] = Field(None, description="Whether this configuration is active")


class ElasticsearchConfigRead(ElasticsearchConfigBase):
    """Schema for reading Elasticsearch configuration (password excluded for security)."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ElasticsearchConfigReadWithPassword(ElasticsearchConfigRead):
    """Schema for reading Elasticsearch configuration with password (admin only)."""
    password: Optional[str] = None
