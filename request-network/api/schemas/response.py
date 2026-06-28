import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Any


class ResponsePublic(BaseModel):
    """
    Schema for displaying a response's public details.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_id: uuid.UUID
    result_count: int | None = None
    received_at: datetime
    has_error: bool = False
    error_message: str | None = None
    execution_time_ms: int | None = None


class ResponseDetailed(ResponsePublic):
    """
    Schema for displaying full response details including result data.
    Used by GET /requests/{id}/response endpoint.
    """
    result_data: dict | str | list | Any | None = None
    is_cached: bool = False
    cache_key: str | None = None