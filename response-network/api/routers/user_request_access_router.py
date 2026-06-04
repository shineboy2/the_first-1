from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth.dependencies import get_current_active_user, get_current_admin_user
from db.session import get_db_session
from models.request_type import RequestType
from models.user import User
from models.request_access import UserRequestAccess
from schemas.request_access import (
    UserRequestAccessCreate,
    UserRequestAccessRead,
    UserRequestAccessUpdate
)

router = APIRouter(prefix="/user-request-access", tags=["user request access"])


@router.post("/", response_model=UserRequestAccessRead, dependencies=[Depends(get_current_admin_user)])
async def create_user_request_access(
    access: UserRequestAccessCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new user request access (Admin only)"""
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == access.user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{access.user_id}' not found"
        )
    
    # Verify request type exists
    request_type_result = await db.execute(select(RequestType).where(RequestType.id == access.request_type_id))
    if not request_type_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RequestType with id '{access.request_type_id}' not found"
        )
    
    # Check if access already exists
    existing = await db.execute(
        select(UserRequestAccess).where(
            UserRequestAccess.user_id == access.user_id,
            UserRequestAccess.request_type_id == access.request_type_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access already exists for this user and request type"
        )
    
    db_access = UserRequestAccess(**access.model_dump())
    db.add(db_access)
    await db.commit()
    await db.refresh(db_access)
    return db_access


@router.get("/", response_model=List[UserRequestAccessRead])
async def list_user_request_access(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user)
):
    """List user request access entries"""
    # Admin sees all, regular users see only their own
    if current_user.is_admin:
        query = select(UserRequestAccess)
    else:
        query = select(UserRequestAccess).where(UserRequestAccess.user_id == current_user.id)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{access_id}", response_model=UserRequestAccessRead)
async def get_user_request_access(
    access_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific user request access entry"""
    result = await db.execute(select(UserRequestAccess).where(UserRequestAccess.id == access_id))
    access = result.scalar_one_or_none()
    
    if not access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"UserRequestAccess with id '{access_id}' not found"
        )
    
    # Check permission
    if not current_user.is_admin and access.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this record"
        )
    
    return access


@router.patch("/{access_id}", response_model=UserRequestAccessRead, dependencies=[Depends(get_current_admin_user)])
async def update_user_request_access(
    access_id: UUID,
    access: UserRequestAccessUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update a user request access entry (Admin only)"""
    result = await db.execute(select(UserRequestAccess).where(UserRequestAccess.id == access_id))
    db_access = result.scalar_one_or_none()
    
    if not db_access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"UserRequestAccess with id '{access_id}' not found"
        )
    
    # Update fields
    for field, value in access.model_dump(exclude_unset=True).items():
        setattr(db_access, field, value)
    
    await db.commit()
    await db.refresh(db_access)
    return db_access


@router.delete("/{access_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_admin_user)])
async def delete_user_request_access(
    access_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a user request access entry (Admin only)"""
    result = await db.execute(select(UserRequestAccess).where(UserRequestAccess.id == access_id))
    access = result.scalar_one_or_none()
    
    if not access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"UserRequestAccess with id '{access_id}' not found"
        )
    
    await db.delete(access)
    await db.commit()