"""
Pydantic schemas for File Request Configuration.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field


# ────── Response Parser Sub-schemas ──────

class ErrorDetectionConfig(BaseModel):
    """Configuration for detecting errors in JSON responses."""
    enabled: bool = False
    error_indicator_path: Optional[str] = Field(
        None, description="Dot-notation path to error indicator field (e.g. 'meta.status')"
    )
    error_values: Optional[List[str]] = Field(
        None, description="Values that indicate an error (e.g. ['ERROR', 'FAILED', '0'])"
    )
    error_message_path: Optional[str] = Field(
        None, description="Dot-notation path to error message field (e.g. 'meta.errorMessage')"
    )


class PostProcessingConfig(BaseModel):
    """Post-processing options for parsed response data."""
    flatten_nested: bool = Field(True, description="Flatten nested objects in extracted data")
    null_handling: str = Field(
        "keep",
        description="How to handle null values: 'keep', 'remove', 'default_empty_string'"
    )
    include_unmapped: bool = Field(
        False,
        description="Include keys not in extract_keys mapping (pass-through all data)"
    )


class ResponseParserConfig(BaseModel):
    """
    Full configuration for parsing JSON responses.
    
    Example:
    {
        "data_root": "data.results",
        "extract_keys": {
            "national_code": "nationalCode",
            "full_name": "person.fullName"
        },
        "error_detection": {
            "enabled": true,
            "error_indicator_path": "meta.status",
            "error_values": ["ERROR"],
            "error_message_path": "meta.errorMessage"
        }
    }
    """
    data_root: str = Field(
        "",
        description="Dot-notation path to the main data in the response JSON. Empty string = root level."
    )
    extract_keys: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of output_name → source_dot_path for extracting specific keys"
    )
    error_detection: Optional[ErrorDetectionConfig] = None
    post_processing: Optional[PostProcessingConfig] = None


# ────── File Request Config Schemas ──────

class FileRequestConfigCreate(BaseModel):
    """Schema for creating a new file request configuration."""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True

    # FTP profiles
    send_ftp_profile_id: UUID
    send_path: str = Field("/outgoing", max_length=500)
    receive_ftp_profile_id: UUID
    receive_path: str = Field("/incoming", max_length=500)

    # File naming
    filename_template: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Template with placeholders like {request_id}, {national_code}, etc."
    )

    # Request content
    content_format: str = Field("json", description="Format: json, csv, text, custom_template")
    content_template: Optional[Any] = None
    content_encoding: str = Field("utf-8", max_length=50)

    # Response parsing
    response_parser_config: Optional[Any] = None

    # Timeout & retry
    response_timeout_minutes: int = Field(1440, ge=1, le=43200)
    max_retries: int = Field(3, ge=0, le=10)
    poll_interval_seconds: int = Field(60, ge=10, le=3600)

    # Error handling
    has_error_response: bool = False


class FileRequestConfigUpdate(BaseModel):
    """Schema for updating a file request configuration. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

    send_ftp_profile_id: Optional[UUID] = None
    send_path: Optional[str] = Field(None, max_length=500)
    receive_ftp_profile_id: Optional[UUID] = None
    receive_path: Optional[str] = Field(None, max_length=500)

    filename_template: Optional[str] = Field(None, min_length=1, max_length=500)
    content_format: Optional[str] = None
    content_template: Optional[Any] = None
    content_encoding: Optional[str] = Field(None, max_length=50)

    response_parser_config: Optional[Any] = None

    response_timeout_minutes: Optional[int] = Field(None, ge=1, le=43200)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    poll_interval_seconds: Optional[int] = Field(None, ge=10, le=3600)

    has_error_response: Optional[bool] = None


class FileRequestConfigRead(BaseModel):
    """Schema for reading file request configuration."""
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    is_active: bool

    send_ftp_profile_id: UUID
    send_path: str
    receive_ftp_profile_id: UUID
    receive_path: str

    filename_template: str
    content_format: str
    content_template: Optional[Any]
    content_encoding: str

    response_parser_config: Optional[Any]

    response_timeout_minutes: int
    max_retries: int
    poll_interval_seconds: int

    has_error_response: bool

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ────── Test Parse Schemas ──────

class TestParseRequest(BaseModel):
    """Input for testing response parser with sample JSON."""
    sample_json: Dict[str, Any] = Field(
        ..., description="Sample JSON response from external system"
    )
    parser_config: ResponseParserConfig = Field(
        ..., description="Parser configuration to test"
    )


class TestParseResponse(BaseModel):
    """Output of test parse operation."""
    success: bool
    extracted_data: Optional[Any] = None
    error: Optional[str] = None
    raw_input: Dict[str, Any]


class TestGenerateRequest(BaseModel):
    """Input for testing file generation."""
    sample_params: Dict[str, Any] = Field(
        ..., description="Sample query_params to test file generation"
    )


class TestGenerateResponse(BaseModel):
    """Output of test file generation."""
    generated_filename: str
    generated_content: str
    content_format: str
