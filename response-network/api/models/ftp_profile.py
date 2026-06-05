"""
FTP Profile model for reusable FTP connection configurations.
Used across the system wherever FTP connectivity is needed.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from shared.database.base import BaseModel, UUIDMixin, TimestampMixin


class FTPProfile(BaseModel, UUIDMixin, TimestampMixin):
    """
    Reusable FTP connection profile.
    Admins can define profiles and reference them in file request configs,
    export/import settings, and other FTP-dependent features.
    """
    __tablename__ = "ftp_profiles"

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

    # ────── Connection Settings ──────
    host: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    port: Mapped[int] = mapped_column(
        Integer, nullable=False, default=21
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    # TODO(security): Password is stored as plain text, matching existing
    # ElasticsearchConfig pattern. Consider adding encryption at rest in a future phase.
    password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    base_path: Mapped[str] = mapped_column(
        String(500), nullable=False, default="/"
    )

    # ────── Protocol Settings ──────
    use_tls: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    passive_mode: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    timeout: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )

    # ────── Status ──────
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )

    # ────── Connection Test Tracking ──────
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_test_result: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )

    def __repr__(self):
        return f"<FTPProfile(name={self.name}, host={self.host}:{self.port})>"
