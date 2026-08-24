from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY

from shared.database.base import BaseModel, UUIDMixin, TimestampMixin


class RequestType(BaseModel, UUIDMixin, TimestampMixin):
    __tablename__ = "request_types"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    max_items_per_request: Mapped[int] = mapped_column(nullable=False, default=100)
    available_indices: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=lambda: ["default"])
    elasticsearch_query_template: Mapped[dict] = mapped_column(JSON, nullable=True, default=lambda: {})

    # Output transformation mappings
    # field_mapping: Rename ES _source keys in the output, e.g. {"name": "نام", "city": "شهر"}
    field_mapping: Mapped[dict] = mapped_column(JSON, nullable=True, default=lambda: {})
    # index_mapping: Alias real index names, e.g. {"hotels_index": "اطلاعات هتل‌ها"}
    index_mapping: Mapped[dict] = mapped_column(JSON, nullable=True, default=lambda: {})

    # Execution method: "elasticsearch" (default), "external_api", "file_request"
    execution_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="elasticsearch"
    )
    # FK to file_request_configs.id — only when execution_method == "file_request"
    file_request_config_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID, ForeignKey("file_request_configs.id"), nullable=True
    )
    # FK to external_apis.id — only when execution_method == "external_api"
    external_api_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID, ForeignKey("external_apis.id"), nullable=True
    )
    # FK to object_storage_configs.id — only when execution_method == "object_storage"
    object_storage_config_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID, ForeignKey("object_storage_configs.id"), nullable=True
    )
    # JSON config for mapping ES result fields to object storage paths
    # Example: {"file_paths": ["photo_path"], "base_prefix": "images/", ...}
    object_storage_mapping: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None
    )

    created_by_id: Mapped[UUID] = mapped_column(PGUUID, ForeignKey("users.id"), nullable=False, default=None)
    created_by: Mapped["User"] = relationship("User", back_populates="created_request_types")

    # Relationships
    parameters: Mapped[List["RequestTypeParameter"]] = relationship("RequestTypeParameter", back_populates="request_type", cascade="all, delete-orphan")
    user_access: Mapped[List["UserRequestAccess"]] = relationship("UserRequestAccess", back_populates="request_type")
    profile_access: Mapped[List["ProfileTypeRequestAccess"]] = relationship("ProfileTypeRequestAccess", back_populates="request_type")
    file_request_config = relationship("FileRequestConfig", foreign_keys=[file_request_config_id])
    external_api_rel = relationship("ExternalAPI", foreign_keys=[external_api_id])
    object_storage_config_rel = relationship("ObjectStorageConfig", foreign_keys=[object_storage_config_id])