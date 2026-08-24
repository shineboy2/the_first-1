"""
Object Storage Configuration model.
Stores connection details for S3-compatible storage systems (Ceph, MinIO, AWS S3).
Used by the object_storage execution method to download objects and convert to base64.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import BaseModel, UUIDMixin, TimestampMixin


class ObjectStorageConfig(BaseModel, UUIDMixin, TimestampMixin):
    """
    Configuration for connecting to S3-compatible object storage (Ceph/MinIO/S3).
    Each config stores endpoint, credentials, and bucket info.
    Secret key is encrypted at rest using Fernet (core.encryption).
    """
    __tablename__ = "object_storage_configs"

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
    storage_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="minio",
        comment="Storage provider type: minio, ceph, s3"
    )
    endpoint_url: Mapped[str] = mapped_column(
        String(500), nullable=False,
        comment="S3-compatible endpoint URL, e.g. http://192.168.1.10:9000"
    )
    access_key: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    # Secret key is stored encrypted via Fernet
    secret_key_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Fernet-encrypted secret key"
    )
    region: Mapped[str] = mapped_column(
        String(50), nullable=False, default="us-east-1"
    )

    # ────── Bucket Settings ──────
    default_bucket: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="Default bucket name to use when not specified in query"
    )

    # ────── Protocol Settings ──────
    use_ssl: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    verify_ssl: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    path_style: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="Use path-style addressing (required for MinIO/Ceph)"
    )
    timeout: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30,
        comment="Connection timeout in seconds"
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

    # ────── Encryption Helpers ──────
    def set_secret_key(self, plain_secret_key: str) -> None:
        """Encrypt and store the secret key."""
        from core.encryption import encrypt_data
        self.secret_key_encrypted = encrypt_data(
            plain_secret_key.encode("utf-8")
        ).decode("utf-8")

    def get_secret_key(self) -> str:
        """Decrypt and return the secret key."""
        from core.encryption import decrypt_data
        return decrypt_data(
            self.secret_key_encrypted.encode("utf-8")
        ).decode("utf-8")

    def to_read(self):
        """Convert to read schema (without secret key)."""
        from schemas.object_storage_config import ObjectStorageConfigRead
        return ObjectStorageConfigRead(
            id=self.id,
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            storage_type=self.storage_type,
            endpoint_url=self.endpoint_url,
            access_key=self.access_key,
            region=self.region,
            default_bucket=self.default_bucket,
            use_ssl=self.use_ssl,
            verify_ssl=self.verify_ssl,
            path_style=self.path_style,
            timeout=self.timeout,
            is_active=self.is_active,
            last_tested_at=self.last_tested_at,
            last_test_result=self.last_test_result,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def __repr__(self):
        return f"<ObjectStorageConfig(name={self.name}, type={self.storage_type}, endpoint={self.endpoint_url})>"
