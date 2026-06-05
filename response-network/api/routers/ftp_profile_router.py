"""
API router for FTP Profile management.
Admin-only endpoints for creating, listing, testing, and managing FTP connection profiles.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from auth.dependencies import get_current_admin_user
from models.user import User
from schemas.ftp_profile import (
    FTPProfileCreate,
    FTPProfileUpdate,
    FTPProfileRead,
    FTPProfileTestResult,
)
import crud.ftp_profiles as crud_ftp
from services.ftp_profile_service import FTPProfileService

router = APIRouter(prefix="/ftp-profiles", tags=["FTP Profiles"])


@router.post("/", response_model=FTPProfileRead, status_code=status.HTTP_201_CREATED)
async def create_ftp_profile(
    profile_in: FTPProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new FTP profile. Admin only."""
    existing = await crud_ftp.get_ftp_profile_by_name(db, profile_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"FTP profile with name '{profile_in.name}' already exists",
        )
    return await crud_ftp.create_ftp_profile(db, profile_in)


@router.get("/", response_model=List[FTPProfileRead])
async def list_ftp_profiles(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """List all FTP profiles. Admin only."""
    return await crud_ftp.get_ftp_profiles(db, skip=skip, limit=limit, active_only=active_only)


@router.get("/{profile_id}", response_model=FTPProfileRead)
async def get_ftp_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get FTP profile details by ID. Admin only."""
    profile = await crud_ftp.get_ftp_profile(db, profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FTP profile not found",
        )
    return profile


@router.patch("/{profile_id}", response_model=FTPProfileRead)
async def update_ftp_profile(
    profile_id: UUID,
    profile_in: FTPProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update an FTP profile. Admin only."""
    # Check name uniqueness if name is being changed
    if profile_in.name is not None:
        existing = await crud_ftp.get_ftp_profile_by_name(db, profile_in.name)
        if existing and existing.id != profile_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"FTP profile with name '{profile_in.name}' already exists",
            )

    updated = await crud_ftp.update_ftp_profile(db, profile_id, profile_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FTP profile not found",
        )
    return updated


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ftp_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete an FTP profile. Admin only."""
    # TODO: Check if profile is referenced by any FileRequestConfig before deleting
    success = await crud_ftp.delete_ftp_profile(db, profile_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FTP profile not found",
        )
    return None


@router.post("/{profile_id}/test", response_model=FTPProfileTestResult)
async def test_ftp_connection(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Test FTP connection for a profile.
    Verifies connectivity, authentication, read and write access.
    Admin only.
    """
    profile = await crud_ftp.get_ftp_profile(db, profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FTP profile not found",
        )
    return await FTPProfileService.test_connection(db, profile_id)
