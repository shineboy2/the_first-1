"""
Users router for Request Network - Read-only access to synced users
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime
import uuid
import secrets

from db.session import get_db_session
from models.user import User
from models.api_key import ApiKey
from pydantic import BaseModel
from auth.dependencies import get_current_active_user, require_admin
from schemas.api_key import APIKeyCreate, APIKeyRead, APIKeyGenerated

from uuid import UUID

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    id: UUID | str
    username: str
    email: str
    full_name: str | None
    profile_type: str
    is_active: bool
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    rate_limit_per_day: int
    daily_request_limit: int
    monthly_request_limit: int
    priority: int
    synced_at: datetime | None
    
    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current logged in user details
    """
    return current_user


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all synced users in Request Network
    """
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific user by ID
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/username/{username}", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a user by username
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ============================================================================
# API Key Endpoints
# ============================================================================

@router.get("/{user_id}/api-keys", response_model=List[APIKeyRead])
async def get_user_api_keys(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin)
):
    """
    Get all API keys for a specific user.
    Admins only.
    """
    # Verify user exists
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    stmt = select(ApiKey).where(ApiKey.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/{user_id}/api-keys", response_model=APIKeyGenerated, status_code=201)
async def create_user_api_key(
    user_id: str,
    api_key_in: APIKeyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin)
):
    """
    Create a new API key for a specific user.
    Admins only.
    """
    from routers.api_key_router import API_KEY_PREFIX, hash_api_key
    
    # Verify user exists
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    plain_key = f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
    hashed_key = hash_api_key(plain_key)

    db_api_key = ApiKey(
        user_id=user_id,
        name=api_key_in.name,
        key_hash=hashed_key,
        prefix=API_KEY_PREFIX,
        scopes=api_key_in.scopes,
    )
    db.add(db_api_key)
    await db.commit()
    await db.refresh(db_api_key)

    return APIKeyGenerated(
        id=db_api_key.id,
        name=db_api_key.name,
        created_at=db_api_key.created_at,
        api_key=plain_key,
    )


@router.delete("/{user_id}/api-keys/{api_key_id}", status_code=204)
async def revoke_user_api_key(
    user_id: str,
    api_key_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin)
):
    """
    Revoke an API key for a specific user.
    Admins only.
    """
    stmt = select(ApiKey).where(ApiKey.id == api_key_id, ApiKey.user_id == user_id)
    result = await db.execute(stmt)
    db_api_key = result.scalars().first()

    if not db_api_key:
        raise HTTPException(status_code=404, detail="API Key not found")

    db_api_key.is_active = False
    db.add(db_api_key)
    await db.commit()
    return None

