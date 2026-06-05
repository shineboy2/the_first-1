"""
CRUD operations for File Request Configurations.
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.file_request_config import FileRequestConfig
from schemas.file_request_config import FileRequestConfigCreate, FileRequestConfigUpdate


async def create_file_request_config(
    db: AsyncSession, config_in: FileRequestConfigCreate
) -> FileRequestConfig:
    """Create a new file request configuration."""
    db_obj = FileRequestConfig(**config_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_file_request_config(
    db: AsyncSession, config_id: UUID
) -> Optional[FileRequestConfig]:
    """Get a file request config by ID."""
    return await db.get(FileRequestConfig, config_id)


async def get_file_request_config_by_name(
    db: AsyncSession, name: str
) -> Optional[FileRequestConfig]:
    """Get a file request config by unique name."""
    result = await db.execute(
        select(FileRequestConfig).where(FileRequestConfig.name == name)
    )
    return result.scalar_one_or_none()


async def get_file_request_configs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False
) -> List[FileRequestConfig]:
    """Get list of file request configurations."""
    query = select(FileRequestConfig)
    if active_only:
        query = query.where(FileRequestConfig.is_active == True)
    query = query.order_by(FileRequestConfig.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_file_request_config(
    db: AsyncSession,
    config_id: UUID,
    config_in: FileRequestConfigUpdate
) -> Optional[FileRequestConfig]:
    """Update a file request configuration."""
    db_obj = await db.get(FileRequestConfig, config_id)
    if not db_obj:
        return None

    update_data = config_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_file_request_config(db: AsyncSession, config_id: UUID) -> bool:
    """Delete a file request configuration. Returns True if deleted."""
    db_obj = await db.get(FileRequestConfig, config_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True
