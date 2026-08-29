import uuid
from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.session import get_db_session
from db.redis_client import get_redis_client
from auth.dependencies import require_admin, get_current_user
from models.user import User
from models.api_key import ApiKey
from schemas.user import User as UserSchema
from schemas.api_key import APIKeyCreate, APIKeyRead, APIKeyGenerated
from pydantic import BaseModel
from rate_limiter import RateLimiter
from services.audit_service import create_audit_log
import secrets

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)]
)


@router.get("/users", response_model=List[UserSchema])
async def list_users(
    db: AsyncSession = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = Query(None, description="Filter by active status"),
    profile_type: str | None = Query(None, description="Filter by profile type"),
):
    """
    List all users in the system. Admins only.
    Supports pagination and filtering.
    """
    query = select(User)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if profile_type:
        query = query.where(User.profile_type == profile_type)

    query = query.offset(skip).limit(limit).order_by(User.synced_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()
    return users


class AdminUserDetails(UserSchema):
    rate_limit_stats: Dict[str, Any] = {}

    class Config:
        from_attributes = True


@router.get("/users/{user_id}", response_model=AdminUserDetails)
async def get_user_details(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed information for a specific user, including rate limit stats.
    Admins only.
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    redis_client = await get_redis_client()
    rate_limiter = RateLimiter(redis_client.client)
    stats = await rate_limiter.get_user_stats(str(user.id), user.profile_type)

    user_data = UserSchema.model_validate(user).model_dump()
    user_data["rate_limit_stats"] = stats
    return user_data


@router.post("/users/{user_id}/activate", response_model=UserSchema)
async def activate_user(
    request: Request,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_user)
):
    """
    Activate a user account. Admins only.
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already active")

    user.is_active = True
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    await create_audit_log(db, "USER_ACTIVATED", request, user_id=current_admin.id, resource_type="User", resource_id=str(user_id))
    
    return user


@router.post("/users/{user_id}/deactivate", response_model=UserSchema)
async def deactivate_user(
    request: Request,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_user)
):
    """
    Deactivate a user account. Admins only.
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already inactive")

    user.is_active = False
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    await create_audit_log(db, "USER_DEACTIVATED", request, user_id=current_admin.id, resource_type="User", resource_id=str(user_id))
    
    return user


class UserIPUpdate(BaseModel):
    allowed_ips: List[str]

@router.put("/users/{user_id}/allowed-ips", response_model=UserSchema)
async def update_user_allowed_ips(
    request: Request,
    user_id: uuid.UUID,
    ip_update: UserIPUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_user)
):
    """
    Update a user's allowed IPs. Admins only.
    Note: Changes here might be overwritten by sync from Response Network 
    unless also updated there.
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.allowed_ips = ip_update.allowed_ips
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    await create_audit_log(db, "USER_ALLOWED_IPS_UPDATED", request, user_id=current_admin.id, resource_type="User", resource_id=str(user_id), meta={"allowed_ips": ip_update.allowed_ips})
    
    return user



# ============ NO PASSWORD MANAGEMENT HERE ============
# Password changes are automatically synced from Response Network
# via the settings_importer task - see workers/tasks/settings_importer.py

@router.get("/users/{user_id}/api-keys", response_model=List[APIKeyRead])
async def get_user_api_keys_admin(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """Get all API keys for a specific user. Admins only."""
    stmt = select(ApiKey).where(ApiKey.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/users/{user_id}/api-keys", response_model=APIKeyGenerated, status_code=status.HTTP_201_CREATED)
async def create_user_api_key_admin(
    request: Request,
    user_id: uuid.UUID,
    api_key_in: APIKeyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_user)
):
    """Create a new API key for a specific user. Admins only."""
    from routers.api_key_router import API_KEY_PREFIX, hash_api_key
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
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

    
    await create_audit_log(db, "API_KEY_CREATED", request, user_id=current_admin.id, resource_type="ApiKey", resource_id=str(db_api_key.id), meta={"name": api_key_in.name, "target_user_id": str(user_id)})

    return APIKeyGenerated(
        id=db_api_key.id,
        name=db_api_key.name,
        created_at=db_api_key.created_at,
        api_key=plain_key,
    )


@router.delete("/users/{user_id}/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_user_api_key_admin(
    request: Request,
    user_id: uuid.UUID,
    api_key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_user)
):
    """Revoke an API key for a specific user. Admins only."""
    stmt = select(ApiKey).where(ApiKey.id == api_key_id, ApiKey.user_id == user_id)
    result = await db.execute(stmt)
    db_api_key = result.scalars().first()

    if not db_api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")

    db_api_key.is_active = False
    await db.commit()
    
    await create_audit_log(db, "API_KEY_REVOKED", request, user_id=current_admin.id, resource_type="ApiKey", resource_id=str(api_key_id), meta={"target_user_id": str(user_id)})
    
    return None