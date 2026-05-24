# -*- coding: utf-8 -*-
import uuid
from sqlalchemy import Column, DateTime, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, declared_attr


class_registry: dict = {}
Base = declarative_base(class_registry=class_registry)


class UUIDMixin:
    """
    Mixin that adds a UUID primary key column to a model.
    """
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)




class TimestampMixin:
    """
    Mixin that adds created_at and updated_at columns to a model.
    """
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BaseModel(Base):
    """
    Base model class that provides common functionality.
    Note: Use UUIDMixin and TimestampMixin to add id and timestamp fields.
    """
    __abstract__ = True