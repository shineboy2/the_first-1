"""
Object Storage Configuration router.
Provides CRUD endpoints + connection test for S3-compatible storage configs.
Follows the same pattern as elasticsearch_config router.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db_session
from auth.dependencies import get_current_admin_user
from models.user import User
from models.object_storage_config import ObjectStorageConfig
from schemas.object_storage_config import (
    ObjectStorageConfigCreate,
    ObjectStorageConfigRead,
    ObjectStorageConfigUpdate,
)
from services.object_storage_config_service import ObjectStorageConfigService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/object-storage",
    tags=["admin-object-storage"],
)


@router.get("/config", response_model=list[ObjectStorageConfigRead])
async def list_object_storage_configs(
    skip: int = 0,
    limit: int = 100,
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
    current_user: Annotated[User, Depends(get_current_admin_user)] = None,
):
    """List all Object Storage configurations."""
    service = ObjectStorageConfigService(db)
    configs = await service.get_all_configs(skip=skip, limit=limit)
    return [config.to_read() for config in configs]


@router.get("/config/active", response_model=ObjectStorageConfigRead)
async def get_active_object_storage_config(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    """Get the currently active Object Storage configuration."""
    service = ObjectStorageConfigService(db)
    config = await service.get_active_config()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Object Storage configuration found",
        )

    return config.to_read()


@router.get("/config/{config_id}", response_model=ObjectStorageConfigRead)
async def get_object_storage_config(
    config_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    """Get a specific Object Storage configuration by ID."""
    service = ObjectStorageConfigService(db)
    config = await service.get_config_by_id(config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Object Storage configuration not found",
        )

    return config.to_read()


@router.post(
    "/config",
    response_model=ObjectStorageConfigRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_object_storage_config(
    data: ObjectStorageConfigCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    """Create a new Object Storage configuration."""
    service = ObjectStorageConfigService(db)

    # Check for duplicate name
    existing = await service.get_config_by_name(data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Object Storage configuration with name '{data.name}' already exists",
        )

    config = await service.create_config(data)
    logger.info(f"Created Object Storage configuration: {config.id} ({config.name})")

    return config.to_read()


@router.put("/config/{config_id}", response_model=ObjectStorageConfigRead)
async def update_object_storage_config(
    config_id: str,
    data: ObjectStorageConfigUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    """Update an Object Storage configuration."""
    service = ObjectStorageConfigService(db)

    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Object Storage configuration not found",
        )

    # Check name uniqueness if name is being updated
    if data.name and data.name != config.name:
        existing = await service.get_config_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Object Storage configuration with name '{data.name}' already exists",
            )

    updated = await service.update_config(config_id, data)
    logger.info(f"Updated Object Storage configuration: {config_id}")

    return updated.to_read()


@router.delete("/config/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object_storage_config(
    config_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    """Delete an Object Storage configuration."""
    service = ObjectStorageConfigService(db)

    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Object Storage configuration not found",
        )

    if config.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete an active Object Storage configuration. Deactivate it first.",
        )

    await service.delete_config(config_id)
    logger.info(f"Deleted Object Storage configuration: {config_id}")


@router.post("/config/{config_id}/test", response_model=dict)
async def test_object_storage_config(
    config_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    """Test connection to Object Storage with a specific configuration."""
    service = ObjectStorageConfigService(db)

    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Object Storage configuration not found",
        )

    success, message = await service.test_connection(config)

    return {
        "success": success,
        "message": message,
        "config_id": config_id,
    }


@router.post("/config/test-new", response_model=dict)
async def test_new_object_storage_config(
    data: ObjectStorageConfigCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
):
    """Test connection with a new (not yet saved) Object Storage configuration."""
    # Create a temporary config object for testing
    config_data = data.model_dump(exclude={"secret_key"})
    temp_config = ObjectStorageConfig(**config_data)
    temp_config.set_secret_key(data.secret_key)

    try:
        from services.object_storage_handler import ObjectStorageHandler

        handler = ObjectStorageHandler(temp_config)
        success, message = handler.test_connection()

        return {
            "success": success,
            "message": message,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}",
        }
