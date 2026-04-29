import secrets
import hashlib
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.session import get_db_session
from models.user import User
from models.api_key import ApiKey as APIKey
from schemas.api_key import APIKeyCreate, APIKeyRead, APIKeyGenerated
from auth.dependencies import get_current_active_user
from .shared.logger import get_logger

router = APIRouter(prefix="/api-keys", tags=["API Keys"])
log = get_logger(__name__)

API_KEY_PREFIX = "sk_live_"


def hash_api_key(api_key: str) -> str:
    """Hashes the API key using SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()


@router.post("/", response_model=APIKeyGenerated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_in: APIKeyCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate a new API key for the current user.
    The key is returned only once upon creation.
    """
    # Generate a secure random key
    plain_key = f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
    hashed_key = hash_api_key(plain_key)

    db_api_key = APIKey(
        user_id=current_user.id,
        name=api_key_in.name,
        key_hash=hashed_key,
        prefix=API_KEY_PREFIX,
        scopes=api_key_in.scopes,
    )
    db.add(db_api_key)
    await db.commit()
    await db.refresh(db_api_key)

    log.info("API Key created", user_id=current_user.id, api_key_id=db_api_key.id)

    return APIKeyGenerated(
        id=db_api_key.id,
        name=db_api_key.name,
        created_at=db_api_key.created_at,
        api_key=plain_key, # Return the plain key only once
    )


@router.get("/", response_model=List[APIKeyRead])
async def get_user_api_keys(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve all active API keys for the current user.
    """
    stmt = select(APIKey).where(APIKey.user_id == current_user.id, APIKey.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """
    Revoke (deactivate) an API key.
    """
    stmt = select(APIKey).where(APIKey.id == api_key_id, APIKey.user_id == current_user.id)
    result = await db.execute(stmt)
    db_api_key = result.scalars().first()

    if not db_api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")

    db_api_key.is_active = False
    await db.commit()
    log.info("API Key revoked", user_id=current_user.id, api_key_id=api_key_id)