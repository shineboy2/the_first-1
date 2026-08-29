"""
Profile Type Request Access Router
Manages access rules for profile types to request types
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from typing import List
from uuid import UUID

from auth.dependencies import get_current_user
from core.dependencies import get_db
from models.user import User
from models.profile_type_request_access import ProfileTypeRequestAccess
from models.profile_type_config import ProfileTypeConfig
from models.request_type import RequestType
from schemas.profile_type_access import (
    ProfileTypeAccessCreate,
    ProfileTypeAccessUpdate,
    ProfileTypeAccessRead,
    BulkProfileTypeAccessCreate
)
from services.audit_service import create_audit_log


router = APIRouter(
    prefix="/request-types",
    tags=["request-types"],
)


@router.post("/{request_type_id}/profile-access", response_model=List[ProfileTypeAccessRead])
async def grant_profile_type_access(
    request: Request,
    request_type_id: UUID,
    data: BulkProfileTypeAccessCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Grant access to multiple profile types for this request type.
    Only admin users can grant access.
    """
    # Verify request type exists
    db_obj = await db.get(RequestType, request_type_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request type with ID {request_type_id} not found"
        )
    
    # Verify profile types exist
    profile_types = await db.execute(
        select(ProfileTypeConfig).where(ProfileTypeConfig.name.in_(data.profile_type_ids))
    )
    found_profiles = {pt.name: pt for pt in profile_types.scalars().all()}
    
    missing_profiles = set(data.profile_type_ids) - set(found_profiles.keys())
    if missing_profiles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile types not found: {', '.join(str(pid) for pid in missing_profiles)}"
        )
    
    # Remove existing access for these profile types
    await db.execute(
        delete(ProfileTypeRequestAccess).where(and_(
            ProfileTypeRequestAccess.request_type_id == request_type_id,
            ProfileTypeRequestAccess.profile_type_id.in_(data.profile_type_ids)
        ))
    )
    
    # Create new access records
    access_records = []
    for profile_type_id in data.profile_type_ids:
        access = ProfileTypeRequestAccess(
            profile_type_id=profile_type_id,
            request_type_id=request_type_id,
            max_requests_per_day=data.max_requests_per_day,
            max_requests_per_month=data.max_requests_per_month,
            is_active=data.is_active
        )
        db.add(access)
        access_records.append(access)
    
    await db.commit()
    for record in access_records:
        await db.refresh(record)
    
    # Add profile type names
    result = []
    for record in access_records:
        profile = found_profiles[record.profile_type_id]
        result.append(ProfileTypeAccessRead(
            id=record.id,
            profile_type_id=record.profile_type_id,
            request_type_id=record.request_type_id,
            max_requests_per_day=record.max_requests_per_day,
            max_requests_per_month=record.max_requests_per_month,
            is_active=record.is_active,
            profile_type_name=profile.display_name,
            created_at=record.created_at,
            updated_at=record.updated_at
        ))
    
    await create_audit_log(db, "PROFILE_ACCESS_GRANTED", request, user_id=current_user.id, resource_type="RequestType", resource_id=str(request_type_id), meta={"profile_type_ids": data.profile_type_ids})
    
    return result


@router.get("/{request_type_id}/profile-access", response_model=List[ProfileTypeAccessRead])
async def list_profile_type_access(
    request_type_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all profile types that have access to this request type.
    Only admin users can view access list.
    """
    result = await db.execute(
        select(ProfileTypeRequestAccess, ProfileTypeConfig)
        .join(ProfileTypeConfig, ProfileTypeRequestAccess.profile_type_id == ProfileTypeConfig.name)
        .where(ProfileTypeRequestAccess.request_type_id == request_type_id)
    )
    
    access_list = []
    for access, profile in result.all():
        access_list.append(ProfileTypeAccessRead(
            id=access.id,
            profile_type_id=access.profile_type_id,
            request_type_id=access.request_type_id,
            max_requests_per_day=access.max_requests_per_day,
            max_requests_per_month=access.max_requests_per_month,
            is_active=access.is_active,
            profile_type_name=profile.display_name,
            created_at=access.created_at,
            updated_at=access.updated_at
        ))
    
    return access_list


@router.put("/{request_type_id}/profile-access/{profile_type_id}", response_model=ProfileTypeAccessRead)
async def update_profile_type_access(
    request: Request,
    request_type_id: UUID,
    profile_type_id: UUID,
    data: ProfileTypeAccessUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update access limits for a specific profile type.
    Only admin users can update access.
    """
    result = await db.execute(
        select(ProfileTypeRequestAccess, ProfileTypeConfig)
        .join(ProfileTypeConfig, ProfileTypeRequestAccess.profile_type_id == ProfileTypeConfig.name)
        .where(and_(
            ProfileTypeRequestAccess.request_type_id == request_type_id,
            ProfileTypeRequestAccess.profile_type_id == profile_type_id
        ))
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile type access not found"
        )
    
    access, profile = row
    
    # Update fields
    if data.max_requests_per_day is not None:
        access.max_requests_per_day = data.max_requests_per_day
    if data.max_requests_per_month is not None:
        access.max_requests_per_month = data.max_requests_per_month
    if data.is_active is not None:
        access.is_active = data.is_active
    
    await db.commit()
    await db.refresh(access)
    
    return ProfileTypeAccessRead(
        id=access.id,
        profile_type_id=access.profile_type_id,
        request_type_id=access.request_type_id,
        max_requests_per_day=access.max_requests_per_day,
        max_requests_per_month=access.max_requests_per_month,
        is_active=access.is_active,
        profile_type_name=profile.display_name,
        created_at=access.created_at,
        updated_at=access.updated_at
    )
    
    await create_audit_log(db, "PROFILE_ACCESS_UPDATED", request, user_id=current_user.id, resource_type="ProfileTypeRequestAccess", resource_id=str(access.id), meta=data.dict(exclude_unset=True))
    
    return result


@router.delete("/{request_type_id}/profile-access/{profile_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_profile_type_access(
    request: Request,
    request_type_id: UUID,
    profile_type_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke access for a specific profile type.
    Only admin users can revoke access.
    """
    result = await db.execute(
        delete(ProfileTypeRequestAccess).where(and_(
            ProfileTypeRequestAccess.request_type_id == request_type_id,
            ProfileTypeRequestAccess.profile_type_id == profile_type_id
        ))
    )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile type access not found"
        )
    
    await db.commit()
    
    await create_audit_log(db, "PROFILE_ACCESS_REVOKED", request, user_id=current_user.id, resource_type="RequestType", resource_id=str(request_type_id), meta={"profile_type_id": str(profile_type_id)})
