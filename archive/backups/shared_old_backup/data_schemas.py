import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from pydantic import BaseModel, Field


# --- Schemas for data transfer between networks ---

class RequestTransferSchema(BaseModel):
    """
    Defines the structure of a single request record within a batch file.
    """
    request_id: uuid.UUID = Field(..., description="The unique ID of the original request.")
    user_id: uuid.UUID = Field(..., description="The ID of the user who made the request.")
    query_type: str = Field(..., description="The type of query to be executed (e.g., 'match', 'term').")
    query_params: Dict[str, Any] = Field(..., description="The parameters for the Elasticsearch query.")
    priority: int = Field(default=5, ge=1, le=10, description="The priority of the request.")
    timestamp_utc: datetime = Field(..., description="The UTC timestamp when the request was created.")


class ResponseTransferSchema(BaseModel):
    """
    Defines the structure of a single response record within a batch file.
    """
    request_id: uuid.UUID = Field(..., description="The ID of the original request this response corresponds to.")
    result_data: Optional[Union[Dict[str, Any], List[Any]]] = Field(..., description="The data returned from the query execution.")
    execution_time_ms: int = Field(..., description="Total execution time in milliseconds.")
    error_message: Optional[str] = Field(default=None, description="Error message if the query failed.")
    timestamp_utc: datetime = Field(..., description="The UTC timestamp when the response was generated.")
    is_cached_result: bool = Field(default=False, description="Indicates if the result came from cache.")


class BatchMetadataSchema(BaseModel):
    """
    Defines the structure and validation for the .meta file accompanying each batch.
    """
    batch_id: uuid.UUID
    batch_type: str
    record_count: int
    file_size_bytes: int
    checksum_sha256: str = Field(..., min_length=64, max_length=64)
    created_at_utc: datetime