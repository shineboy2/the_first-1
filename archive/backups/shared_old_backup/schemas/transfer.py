from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from typing import Literal


class RequestTransferSchema(BaseModel):
    """
    Schema for a single request record inside a transfer file.
    This defines the contract for data being moved from Request-Network to Response-Network.
    """
    id: UUID = Field(..., description="The original request ID from the Request Network.")
    user_id: UUID = Field(..., description="The ID of the user who made the request.")
    query_type: str = Field(..., description="The type of the query (e.g., 'match', 'term').")
    query_params: dict = Field(..., description="The parameters for the query.")
    priority: int = Field(..., description="The priority of the request, inherited from the user.")
    timestamp: datetime = Field(..., description="The UTC timestamp when the request was created.")


class ResponseTransferSchema(BaseModel):
    """
    Schema for a single response record inside a transfer file.
    This defines the contract for data being moved from Response-Network back to Request-Network.
    """
    original_request_id: UUID = Field(..., description="The ID of the request this response corresponds to.")
    result_data: dict | list | None = Field(..., description="The actual data returned by the query.")
    result_count: int | None = Field(..., description="The number of records in the result.")
    execution_time_ms: int | None = Field(..., description="Total execution time in the response network.")
    elasticsearch_took_ms: int | None = Field(..., description="Time taken by Elasticsearch for the query.")
    cache_hit: bool = Field(..., description="Indicates if the result was served from cache.")
    timestamp: datetime = Field(..., description="The UTC timestamp when the query was executed.")


class EncryptionMetadata(BaseModel):
    """Schema for encryption details within the batch metadata."""
    algorithm: str = "AES-256-GCM"
    key_version: str


class BatchMetadataSchema(BaseModel):
    """
    Schema for the .meta file that accompanies every data batch file.
    """
    batch_id: UUID
    batch_type: Literal["requests", "responses", "users"]
    record_count: int
    file_size_bytes: int
    checksum_sha256: str
    created_at_utc: datetime
    source_network: Literal["request-network", "response-network"]
    destination_network: Literal["request-network", "response-network"]
    encryption: EncryptionMetadata | None = None

    @field_validator('checksum_sha256')
    def is_valid_sha256(cls, v):
        if not (len(v) == 64 and v.isalnum()):
            raise ValueError("Checksum must be a valid 64-character SHA256 hash.")
        return v