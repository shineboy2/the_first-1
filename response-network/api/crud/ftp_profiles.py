"""
CRUD operations for FTP Profiles.
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ftp_profile import FTPProfile
from schemas.ftp_profile import FTPProfileCreate, FTPProfileUpdate


async def create_ftp_profile(db: AsyncSession, profile_in: FTPProfileCreate) -> FTPProfile:
    """Create a new FTP profile."""
    db_obj = FTPProfile(**profile_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_ftp_profile(db: AsyncSession, profile_id: UUID) -> Optional[FTPProfile]:
    """Get an FTP profile by ID."""
    return await db.get(FTPProfile, profile_id)


async def get_ftp_profile_by_name(db: AsyncSession, name: str) -> Optional[FTPProfile]:
    """Get an FTP profile by unique name."""
    result = await db.execute(
        select(FTPProfile).where(FTPProfile.name == name)
    )
    return result.scalar_one_or_none()


async def get_ftp_profiles(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False
) -> List[FTPProfile]:
    """Get list of FTP profiles with optional filtering."""
    query = select(FTPProfile)
    if active_only:
        query = query.where(FTPProfile.is_active == True)
    query = query.order_by(FTPProfile.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_ftp_profile(
    db: AsyncSession,
    profile_id: UUID,
    profile_in: FTPProfileUpdate
) -> Optional[FTPProfile]:
    """Update an FTP profile."""
    db_obj = await db.get(FTPProfile, profile_id)
    if not db_obj:
        return None

    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_ftp_profile(db: AsyncSession, profile_id: UUID) -> bool:
    """Delete an FTP profile. Returns True if deleted."""
    db_obj = await db.get(FTPProfile, profile_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True
