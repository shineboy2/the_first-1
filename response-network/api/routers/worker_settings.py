from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from auth.dependencies import get_current_user
from core.dependencies import get_db
from crud.worker_settings import worker_settings_crud
from schemas.worker_settings import (
    WorkerSettings,
    WorkerSettingsCreate,
    WorkerSettingsUpdate,
)
from services.worker_manager import validate_storage_config, validate_schedule_config

router = APIRouter(
    prefix="/worker-settings",
    tags=["worker-settings"],
    dependencies=[Depends(get_current_user)],
)

@router.get("/", response_model=List[WorkerSettings])
async def list_worker_settings(
    db: AsyncSession = Depends(get_db),
):
    """List all worker settings."""
    return await worker_settings_crud.get_all(db)

@router.get("/{worker_id}", response_model=WorkerSettings)
async def get_worker_settings(
    worker_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get specific worker settings by ID."""
    settings = await worker_settings_crud.get(db, id=worker_id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker settings not found",
        )
    return settings

@router.post("/", response_model=WorkerSettings)
async def create_worker_settings(
    settings_in: WorkerSettingsCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create new worker settings."""
    # Validate storage config
    if not validate_storage_config(settings_in.storage_type, settings_in.storage_config):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid storage configuration",
        )
    
    # Validate schedule config
    if not validate_schedule_config(settings_in.schedule_type, settings_in.schedule_config):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid schedule configuration",
        )
    
    # Check for duplicate worker_name
    existing = await worker_settings_crud.get_by_name(db, name=settings_in.worker_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Worker settings with this name already exists",
        )
    
    return await worker_settings_crud.create(db, obj_in=settings_in)

@router.put("/{worker_id}", response_model=WorkerSettings)
async def update_worker_settings(
    worker_id: UUID,
    settings_in: WorkerSettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update existing worker settings."""
    settings = await worker_settings_crud.get(db, id=worker_id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker settings not found",
        )
    
    # Validate storage config if provided
    if settings_in.storage_type and settings_in.storage_config:
        if not validate_storage_config(settings_in.storage_type, settings_in.storage_config):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid storage configuration",
            )
    
    # Validate schedule config if provided
    if settings_in.schedule_type and settings_in.schedule_config:
        if not validate_schedule_config(settings_in.schedule_type, settings_in.schedule_config):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid schedule configuration",
            )
    
    return await worker_settings_crud.update(db, db_obj=settings, obj_in=settings_in)

@router.delete("/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_worker_settings(
    worker_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete worker settings."""
    settings = await worker_settings_crud.get(db, id=worker_id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker settings not found",
        )
    
    await worker_settings_crud.delete(db, id=worker_id)

@router.post("/{worker_id}/toggle", response_model=WorkerSettings)
async def toggle_worker(
    worker_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Toggle worker active status."""
    settings = await worker_settings_crud.get(db, id=worker_id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker settings not found",
        )
    
    return await worker_settings_crud.update(
        db,
        db_obj=settings,
        obj_in=WorkerSettingsUpdate(is_active=not settings.is_active)
    )

# Test connection endpoint
@router.post("/{worker_id}/test-connection", status_code=status.HTTP_200_OK)
async def test_storage_connection(
    worker_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Test storage connection for worker settings."""
    settings = await worker_settings_crud.get(db, id=worker_id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker settings not found",
        )
    
    try:
        handler = worker_manager.get_storage_handler(
            settings.storage_type,
            settings.storage_config
        )
        await handler.test_connection()
        return {"status": "success", "message": "Connection test successful"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection test failed: {str(e)}",
        )