from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class ExternalAPIBase(BaseModel):
    name: str = Field(..., max_length=100, description="Unique identifier for the API")
    description: Optional[str] = Field(None, max_length=500)
    endpoint_url: str = Field(..., max_length=500, description="The full URL for the API endpoint")
    http_method: str = Field(default="POST", max_length=20)
    is_active: bool = Field(default=True)
    
    # Auth configuration
    auth_type: str = Field(default="none", description="Options: 'none', 'static_key', 'dynamic_token'")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Configuration JSON for dynamic auth tokens")
    static_headers: Optional[Dict[str, Any]] = Field(None, description="Static headers to be added to requests")
    payload_template: Optional[Dict[str, Any]] = Field(None, description="JSON Template for the request body")

class ExternalAPICreate(ExternalAPIBase):
    pass

class ExternalAPIUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    endpoint_url: Optional[str] = Field(None, max_length=500)
    http_method: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    auth_type: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    static_headers: Optional[Dict[str, Any]] = None
    payload_template: Optional[Dict[str, Any]] = None

class ExternalAPIResponse(ExternalAPIBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
