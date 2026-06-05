"""
File Request tracker model.
Tracks the lifecycle of each individual file-based request:
generation → upload → waiting → response → parsing → completion.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database.base import BaseModel, UUIDMixin, TimestampMixin


class FileRequest(BaseModel, UUIDMixin, TimestampMixin):
    """
    Tracks the state and lifecycle of a single file-based request.
    Links an IncomingRequest to its file processing details.
    """
    __tablename__ = "file_requests"

    # ────── References ──────
    incoming_request_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incoming_requests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    file_request_config_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("file_request_configs.id"),
        nullable=False,
        index=True,
    )

    # ────── File Info ──────
    filename: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    file_content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )

    # ────── Status ──────
    # generating → uploading → uploaded → waiting_response →
    # response_received → parsing → completed | failed | timeout
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="generating", index=True
    )

    # ────── Lifecycle Timestamps ──────
    file_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_detected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    parsed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ────── Response Info ──────
    response_filename: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    response_raw_content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    parsed_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    # ────── Error Tracking ──────
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_poll_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    poll_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # ────── Relationships ──────
    incoming_request = relationship(
        "IncomingRequest", backref="file_request"
    )
    config = relationship(
        "FileRequestConfig"
    )

    def __repr__(self):
        return f"<FileRequest(id={self.id}, status={self.status}, filename={self.filename})>"
