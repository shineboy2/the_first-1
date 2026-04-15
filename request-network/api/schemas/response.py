import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ResponsePublic(BaseModel):
    """
    Schema for displaying a response's public details.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_id: uuid.UUID
    result_count: int | None = None
    received_at: datetime


class ResponseDetailed(ResponsePublic):
    """
    Schema for displaying full response details including result data.
    Used by GET /requests/{id}/response endpoint.
    """
    result_data: dict | None = None