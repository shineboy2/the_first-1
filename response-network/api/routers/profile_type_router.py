"""
Router for managing user profile types.
Admin endpoint to create, view, update, and delete profile types.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from auth.dependencies import get_current_admin_user
from core.dependencies import get_db
from models.user import User
from models.profile_type import ProfileType
from schemas.profile_type_config import (
    ProfileTypeConfigCreate,
    ProfileTypeConfigRead,
    ProfileTypeConfigUpdate
)
from crud import profile_type_config as crud_profile_type

router = APIRouter(prefix="/profile-types", tags=["profile types"])

# Built-in profile types that cannot be deleted
BUILTIN_TYPES = {
    "admin": "Admin",
    "user": "User",
    "viewer": "Viewer",
    "basic": "Basic",
    "premium": "Premium",
    "enterprise": "Enterprise"
}


@router.get("", response_model=List[ProfileTypeConfigRead])
async def list_profile_types(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get list of all profile types (both builtin and custom).
    Only accessible to admin users.
    """
    types = await crud_profile_type.list_profile_types(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active
    )
    return types


@router.get("/{name}", response_model=ProfileTypeConfigRead)
async def get_profile_type(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get information about a specific profile type.
    Only accessible to admin users.
    """
    profile_type = await crud_profile_type.get_profile_type(db=db, name=name)
    if not profile_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile type '{name}' not found"
        )
    return profile_type


@router.post("", response_model=ProfileTypeConfigRead, status_code=status.HTTP_201_CREATED)
async def create_profile_type(
    profile_type: ProfileTypeConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new custom profile type.
    Only accessible to admin users.
    
    Profile type names must be unique and cannot conflict with built-in types.
    """
    # Check if name conflicts with builtin types
    if profile_type.name.lower() in BUILTIN_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create profile type with name '{profile_type.name}' - conflicts with built-in type"
        )
    
    # Check if name already exists
    existing = await crud_profile_type.get_profile_type(db=db, name=profile_type.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Profile type '{profile_type.name}' already exists"
        )
    
    created_type = await crud_profile_type.create_profile_type(db=db, profile_type=profile_type)
    return created_type


@router.put("/{name}", response_model=ProfileTypeConfigRead)
async def update_profile_type(
    name: str,
    profile_type_update: ProfileTypeConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update an existing profile type.
    Only accessible to admin users.
    
    Note: Built-in profile types can be updated but not renamed or deleted.
    """
    # Check if type exists
    existing = await crud_profile_type.get_profile_type(db=db, name=name)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile type '{name}' not found"
        )
    
    # Prevent renaming to built-in type or existing type
    if profile_type_update.name and profile_type_update.name != name:
        if profile_type_update.name.lower() in BUILTIN_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot rename to '{profile_type_update.name}' - conflicts with built-in type"
            )
        existing_with_new_name = await crud_profile_type.get_profile_type(
            db=db,
            name=profile_type_update.name
        )
        if existing_with_new_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Profile type '{profile_type_update.name}' already exists"
            )
    
    updated_type = await crud_profile_type.update_profile_type(
        db=db,
        name=name,
        profile_type_update=profile_type_update
    )
    return updated_type


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_type(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a custom profile type.
    Only accessible to admin users.
    
    Built-in profile types cannot be deleted.
    """
    # Prevent deletion of built-in types
    if name.lower() in BUILTIN_TYPES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot delete built-in profile type '{name}'"
        )
    
    # Check if type exists
    existing = await crud_profile_type.get_profile_type(db=db, name=name)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile type '{name}' not found"
        )
    
    try:
        deleted = await crud_profile_type.delete_profile_type(db=db, name=name)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete profile type"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
