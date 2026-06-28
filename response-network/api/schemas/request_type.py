from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class RequestTypeParameterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parameter_type: str = Field(..., min_length=1, max_length=50)
    is_required: bool = False
    validation_rules: Optional[Dict] = None
    placeholder_key: str = Field(..., min_length=1, max_length=100)


class RequestTypeParameterCreate(RequestTypeParameterBase):
    pass


class RequestTypeParameterRead(RequestTypeParameterBase):
    id: UUID
    request_type_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequestTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    is_public: bool = False
    version: str = "1.0.0"
    max_items_per_request: int = Field(100, ge=1, le=1000)
    available_indices: List[str] = Field(default=["default"])
    elasticsearch_query_template: Dict = Field(default_factory=dict, description="Elasticsearch query template with placeholders")
    execution_method: str = Field(default="elasticsearch")
    external_api_id: Optional[UUID] = None
    file_request_config_id: Optional[UUID] = None


# Step 1: Initial creation with name and description
class RequestTypeCreateInitial(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    execution_method: str = Field(default="elasticsearch")
    external_api_id: Optional[UUID] = None
    file_request_config_id: Optional[UUID] = None


# Step 2: Configure parameters and limits
class RequestTypeConfigureParams(BaseModel):
    is_active: Optional[bool] = None
    is_public: bool = False
    max_items_per_request: int = Field(100, ge=1, le=1000)
    available_indices: List[str] = Field(default=["default"])
    parameters: List[RequestTypeParameterCreate]
    execution_method: Optional[str] = None
    external_api_id: Optional[UUID] = None
    file_request_config_id: Optional[UUID] = None


# Step 3: Configure Elasticsearch query
class RequestTypeConfigureQuery(BaseModel):
    elasticsearch_query_template: Dict = Field(
        ..., 
        description="Elasticsearch query template with placeholders"
    )


class RequestTypeRead(RequestTypeBase):
    id: UUID
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    parameters: List[RequestTypeParameterRead]

    class Config:
        from_attributes = True