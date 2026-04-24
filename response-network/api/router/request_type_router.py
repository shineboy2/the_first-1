from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, delete

from models.request_type import RequestType 
from models.request_type_parameter import RequestTypeParameter
from models.user import User
from models.request_access import UserRequestAccess
from models.profile_type_request_access import ProfileTypeRequestAccess
from schemas.request_type import (
    RequestTypeCreateInitial,
    RequestTypeConfigureParams, 
    RequestTypeConfigureQuery,
    RequestTypeRead
)
from schemas.request_access import (
    UserRequestAccessRead,
    BulkUserRequestAccessCreate
)
from schemas.profile_type_request_access import (
    ProfileTypeRequestAccessCreate,
    ProfileTypeRequestAccessRead
)
from auth.dependencies import get_current_admin_user
from core.dependencies import get_db
router = APIRouter(prefix="/request-types", tags=["request-types"])


@router.post("/", response_model=RequestTypeRead, status_code=status.HTTP_201_CREATED)
async def create_request_type_initial(
    data: RequestTypeCreateInitial,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 1: Create a new request type with basic information.
    Only admin users can create request types.
    """
    # Check if request type with same name exists
    existing = await db.execute(
        select(RequestType).where(RequestType.name == data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request type with name '{data.name}' already exists"
        )
    
    # Create request type with minimal info
    db_obj = RequestType(
        name=data.name,
        description=data.description,
        is_active=data.is_active,
        created_by_id=current_user.id
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj, ["parameters"])
    
    return db_obj


@router.put("/{request_type_id}/configure", response_model=RequestTypeRead)
async def configure_request_type_params(
    request_type_id: UUID,
    data: RequestTypeConfigureParams,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2: Configure parameters and settings for the request type.
    Only admin users can configure request types.
    """
    # Get request type
    db_obj = await db.get(RequestType, request_type_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request type with ID {request_type_id} not found"
        )
    
    # Update basic settings
    for field, value in data.model_dump(exclude={"parameters"}).items():
        setattr(db_obj, field, value)
    
    # Update parameters
    # First remove existing parameters
    await db.execute(
        delete(RequestTypeParameter)
        .where(RequestTypeParameter.request_type_id == request_type_id)
    )
    
    # Add new parameters
    for param in data.parameters:
        db_param = RequestTypeParameter(
            **param.model_dump(),
            request_type_id=request_type_id
        )
        db.add(db_param)
        
    await db.commit()
    
    # Re-fetch with parameters loaded
    query = select(RequestType).options(selectinload(RequestType.parameters)).where(RequestType.id == request_type_id)
    result = await db.execute(query)
    db_obj = result.scalar_one()
    
    return db_obj


# Step 3: Configure Elasticsearch query
@router.put("/{request_type_id}/query", response_model=RequestTypeRead)
async def configure_request_type_query(
    request_type_id: UUID,
    data: RequestTypeConfigureQuery,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 3: Configure the Elasticsearch query template.
    Only admin users can configure request types.
    """
    # Get request type with parameters loaded
    query = select(RequestType).options(selectinload(RequestType.parameters)).where(RequestType.id == request_type_id)
    result = await db.execute(query)
    db_obj = result.scalar_one_or_none()
    
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request type with ID {request_type_id} not found"
        )
    
    # Update query template
    db_obj.elasticsearch_query_template = data.elasticsearch_query_template
    
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


# User Access Management
@router.post("/{request_type_id}/access", response_model=List[UserRequestAccessRead])
async def grant_access_to_users(
    request_type_id: UUID,
    data: BulkUserRequestAccessCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Grant access to multiple users for this request type.
    Only admin users can grant access.
    """
    # Get request type
    db_obj = await db.get(RequestType, request_type_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request type with ID {request_type_id} not found"
        )
    
    # Verify users exist
    users = await db.execute(
        select(User).where(User.id.in_(data.user_ids))
    )
    found_users = {user.id: user for user in users.scalars().all()}
    
    missing_users = set(data.user_ids) - set(found_users.keys())
    if missing_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Users not found: {', '.join(str(uid) for uid in missing_users)}"
        )
    
    # Remove existing access for these users
    await db.execute(
        delete(UserRequestAccess).where(and_(
            UserRequestAccess.request_type_id == request_type_id,
            UserRequestAccess.user_id.in_(data.user_ids)
        ))
    )
    
    # Create new access records
    for user_id in data.user_ids:
        access = UserRequestAccess(
            user_id=user_id,
            request_type_id=request_type_id,
            max_requests_per_hour=data.max_requests_per_hour,
            is_active=data.is_active
        )
        db.add(access)
    
    await db.commit()
    
    # Query the created records with eager-loaded user relationship
    # This prevents MissingGreenlet error when Pydantic tries to serialize the user field
    result = await db.execute(
        select(UserRequestAccess)
        .options(selectinload(UserRequestAccess.user))
        .where(and_(
            UserRequestAccess.request_type_id == request_type_id,
            UserRequestAccess.user_id.in_(data.user_ids)
        ))
    )
    
    return result.scalars().all()


@router.get("/{request_type_id}/access", response_model=List[UserRequestAccessRead])
async def list_user_access(
    request_type_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users that have access to this request type.
    Only admin users can view access list.
    """
    result = await db.execute(
        select(UserRequestAccess)
        .options(selectinload(UserRequestAccess.user))
        .where(UserRequestAccess.request_type_id == request_type_id)
    )
    return result.scalars().all()


@router.delete("/{request_type_id}/access/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_user_access(
    request_type_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke a user's access to this request type.
    Only admin users can revoke access.
    """
    result = await db.execute(
        delete(UserRequestAccess).where(and_(
            UserRequestAccess.request_type_id == request_type_id,
            UserRequestAccess.user_id == user_id
        ))
    )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No access found for user {user_id} on request type {request_type_id}"
        )
    
    await db.commit()
    return None


@router.get("/", response_model=List[RequestTypeRead])
async def list_request_types(
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all request types. Only admin users can list all request types."""
    query = select(RequestType).options(selectinload(RequestType.parameters))
    if not include_inactive:
        query = query.where(RequestType.is_active == True)
    
    query = query.order_by(RequestType.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{request_type_id}", response_model=RequestTypeRead)
async def get_request_type(
    request_type_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific request type by ID."""
    query = select(RequestType).options(selectinload(RequestType.parameters)).where(RequestType.id == request_type_id)
    result = await db.execute(query)
    db_obj = result.scalar_one_or_none()
    
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request type with ID {request_type_id} not found"
        )
    return db_obj


@router.delete("/{request_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_request_type(
    request_type_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a request type by setting is_active=False (admin only)."""
    db_obj = await db.get(RequestType, request_type_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request type with ID {request_type_id} not found"
        )
    
    db_obj.is_active = False
    await db.commit()
    return None


@router.post("/{request_type_id}/profile-access", response_model=List[ProfileTypeRequestAccessRead])
async def grant_profile_type_access(
    request_type_id: UUID,
    data: ProfileTypeRequestAccessCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Grant access to multiple profile types for this request type.
    Only admin users can grant access.
    """
    # Get request type
    db_obj = await db.get(RequestType, request_type_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request type with ID {request_type_id} not found"
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
    for pt_id in data.profile_type_ids:
        access = ProfileTypeRequestAccess(
            profile_type_id=pt_id,
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
    
    return access_records


@router.get("/{request_type_id}/profile-access", response_model=List[ProfileTypeRequestAccessRead])
async def list_profile_type_access(
    request_type_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all profile types that have access to this request type.
    Only admin users can view access list.
    """
    result = await db.execute(
        select(ProfileTypeRequestAccess)
        .where(ProfileTypeRequestAccess.request_type_id == request_type_id)
    )
    return result.scalars().all()


@router.delete("/{request_type_id}/profile-access/{profile_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_profile_type_access(
    request_type_id: UUID,
    profile_type_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke a profile type's access to this request type.
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
            detail=f"No access found for profile type {profile_type_id} on request type {request_type_id}"
        )
    
    await db.commit()
    return None