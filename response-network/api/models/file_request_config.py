"""
File Request Configuration model.
Defines how file-based requests are generated, sent via FTP,
and how JSON responses are parsed.
"""
import uuid
from typing import Optional, Dict, Any

from sqlalchemy import String, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from shared.database.base import BaseModel, UUIDMixin, TimestampMixin


class FileRequestConfig(BaseModel, UUIDMixin, TimestampMixin):
    """
    Configuration for a type of file-based request.
    Each config defines: FTP endpoints, file naming, content format,
    response parsing rules, and timeout settings.
    """
    __tablename__ = "file_request_configs"

    # ────── Identity ──────
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )

    # ────── FTP Profiles (separate for send and receive) ──────
    send_ftp_profile_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ftp_profiles.id"), nullable=False
    )
    send_path: Mapped[str] = mapped_column(
        String(500), nullable=False, default="/outgoing"
    )
    receive_ftp_profile_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ftp_profiles.id"), nullable=False
    )
    receive_path: Mapped[str] = mapped_column(
        String(500), nullable=False, default="/incoming"
    )

    # ────── File Naming ──────
    # Template with placeholders: {request_id}, {request_type}, {timestamp},
    # {date}, {uuid}, and any key from query_params
    # Example: "INQ_{national_code}_{date:%Y%m%d}.json"
    filename_template: Mapped[str] = mapped_column(
        String(500), nullable=False
    )

    # ────── Request Content ──────
    # Format of the outgoing request file
    content_format: Mapped[str] = mapped_column(
        String(50), nullable=False, default="json"
    )
    # Template for generating file content — JSON with {{placeholder}} for values
    # Example JSON: {"national_code": "{{national_code}}", "date": "{{date}}"}
    # Example CSV: {"headers": ["code"], "row_template": "{{national_code}}"}
    content_template: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    content_encoding: Mapped[str] = mapped_column(
        String(50), nullable=False, default="utf-8"
    )

    # ────── Response Parsing (JSON focused) ──────
    # Full parser configuration — see implementation_plan for detailed schema:
    # {
    #   "data_root": "data.results",         # dot-notation path to main data
    #   "extract_keys": {                     # output_name → source_path mapping
    #     "کد_ملی": "nationalCode",
    #     "نام": "person.fullName"
    #   },
    #   "error_detection": {                  # optional error detection
    #     "enabled": true,
    #     "error_indicator_path": "meta.status",
    #     "error_values": ["ERROR", "FAILED"],
    #     "error_message_path": "meta.errorMessage"
    #   },
    #   "post_processing": {                  # optional post-processing
    #     "flatten_nested": true,
    #     "null_handling": "keep",
    #     "include_unmapped": false
    #   }
    # }
    response_parser_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    # ────── Timeout & Retry ──────
    response_timeout_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1440  # 24 hours
    )
    max_retries: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3
    )
    poll_interval_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )

    # ────── Error Handling ──────
    # Whether the external system sends error responses in the response file
    has_error_response: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # ────── Relationships ──────
    send_ftp_profile = relationship(
        "FTPProfile", foreign_keys=[send_ftp_profile_id]
    )
    receive_ftp_profile = relationship(
        "FTPProfile", foreign_keys=[receive_ftp_profile_id]
    )

    def __repr__(self):
        return f"<FileRequestConfig(name={self.name})>"
