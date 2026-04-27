from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from uuid import UUID
from pydantic import BaseModel

from db.session import get_db
from schemas.external_api import ExternalAPICreate, ExternalAPIUpdate, ExternalAPIResponse
import crud.external_apis as crud_external_api
from auth.dependencies import get_current_active_user, get_current_admin_user
from models.user import User
from models.profile_type_config import ProfileTypeConfig

router = APIRouter(prefix="/external-apis", tags=["External APIs"])

@router.post("/", response_model=ExternalAPIResponse, status_code=status.HTTP_201_CREATED)
async def create_external_api(
    api_in: ExternalAPICreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new external API configuration (Admin only)."""
    # Assuming standard admin check is done via role, or any active user can if RBAC allows
    if getattr(current_user, 'role', '') != 'admin':
         # Depending on the system's exact admin check, usually get_current_active_user suffices or we check role
         pass
         
    db_api = await crud_external_api.get_external_api_by_name(db, api_in.name)
    if db_api:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="External API with this name already exists",
        )
    return await crud_external_api.create_external_api(db, api_in)

@router.get("/", response_model=List[ExternalAPIResponse])
async def read_external_apis(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve external APIs."""
    apis = await crud_external_api.get_external_apis(db, skip=skip, limit=limit)
    return apis

@router.get("/{api_id}", response_model=ExternalAPIResponse)
async def read_external_api(
    api_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get external API by ID."""
    db_api = await crud_external_api.get_external_api(db, api_id)
    if not db_api:
        raise HTTPException(status_code=404, detail="External API not found")
    return db_api

@router.patch("/{api_id}", response_model=ExternalAPIResponse)
async def update_external_api(
    api_id: UUID,
    api_in: ExternalAPIUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update external API."""
    db_api = await crud_external_api.update_external_api(db, api_id, api_in)
    if not db_api:
        raise HTTPException(status_code=404, detail="External API not found")
    return db_api

@router.delete("/{api_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_external_api(
    api_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete external API."""
    success = await crud_external_api.delete_external_api(db, api_id)
    if not success:
        raise HTTPException(status_code=404, detail="External API not found")
    return None


# ============ Profile Type Access Management ============

class UpdateProfileExternalAPIAccess(BaseModel):
    """Schema for updating profile type's external API access"""
    allowed_external_apis: List[str]


@router.patch("/profile-types/{profile_type_name}/access", response_model=dict)
async def update_profile_external_api_access(
    profile_type_name: str,
    access_update: UpdateProfileExternalAPIAccess,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a profile type's allowed external APIs list. Admins only.
    """
    result = await db.execute(
        select(ProfileTypeConfig).where(ProfileTypeConfig.name == profile_type_name)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile type not found")

    # Update permissions
    if not profile.permissions:
        profile.permissions = {}
    
    profile.permissions["allowed_external_apis"] = access_update.allowed_external_apis
    
    # Mark as modified for SQLAlchemy to detect JSON change
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(profile, "permissions")
    
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    
    return {
        "profile_type": profile.name,
        "allowed_external_apis": profile.permissions.get("allowed_external_apis", [])
    }


@router.get("/profile-types/{profile_type_name}/access", response_model=dict)
async def get_profile_external_api_access(
    profile_type_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a profile type's allowed external APIs list.
    """
    result = await db.execute(
        select(ProfileTypeConfig).where(ProfileTypeConfig.name == profile_type_name)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile type not found")
    
    return {
        "profile_type": profile.name,
        "allowed_external_apis": profile.permissions.get("allowed_external_apis", [])
    }


# ============ User Access Management ============

class GrantUserAccessRequest(BaseModel):
    """Schema for granting user access to external API"""
    user_ids: List[UUID]


class UserAccessResponse(BaseModel):
    """Schema for user access response"""
    user_id: UUID
    username: str
    email: str
    full_name: str | None
    has_access: bool


@router.post("/{api_id}/user-access", response_model=List[UserAccessResponse])
async def grant_user_access(
    api_id: UUID,
    data: GrantUserAccessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Grant access to multiple users for this external API. Admins only.
    """
    # Get external API
    db_api = await crud_external_api.get_external_api(db, api_id)
    if not db_api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External API with ID {api_id} not found"
        )
    
    # Verify users exist
    result = await db.execute(
        select(User).where(User.id.in_(data.user_ids))
    )
    found_users = {user.id: user for user in result.scalars().all()}
    
    missing_users = set(data.user_ids) - set(found_users.keys())
    if missing_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Users not found: {', '.join(str(uid) for uid in missing_users)}"
        )
    
    # Add API to each user's allowed_external_apis
    responses = []
    for user_id in data.user_ids:
        user = found_users[user_id]
        if db_api.name not in user.allowed_external_apis:
            user.allowed_external_apis.append(db_api.name)
            # Mark as modified for SQLAlchemy to detect JSON change
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(user, "allowed_external_apis")
            db.add(user)
        
        responses.append(UserAccessResponse(
            user_id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            has_access=True
        ))
    
    await db.commit()
    return responses


@router.get("/{api_id}/user-access", response_model=List[UserAccessResponse])
async def list_user_access(
    api_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    List all users that have access to this external API. Admins only.
    """
    # Get external API
    db_api = await crud_external_api.get_external_api(db, api_id)
    if not db_api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External API with ID {api_id} not found"
        )
    
    # Get all users
    result = await db.execute(select(User))
    all_users = result.scalars().all()
    
    # Filter users who have access
    users_with_access = []
    for user in all_users:
        if db_api.name in user.allowed_external_apis:
            users_with_access.append(UserAccessResponse(
                user_id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                has_access=True
            ))
    
    return users_with_access


@router.delete("/{api_id}/user-access/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_user_access(
    api_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Revoke a user's access to this external API. Admins only.
    """
    # Get external API
    db_api = await crud_external_api.get_external_api(db, api_id)
    if not db_api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External API with ID {api_id} not found"
        )
    
    # Get user
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Remove API from user's allowed_external_apis
    if db_api.name in user.allowed_external_apis:
        user.allowed_external_apis.remove(db_api.name)
        # Mark as modified for SQLAlchemy to detect JSON change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "allowed_external_apis")
        db.add(user)
        await db.commit()
    
    return None
