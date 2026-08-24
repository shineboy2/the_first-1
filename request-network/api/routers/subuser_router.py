import uuid
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.session import get_db_session
from auth.dependencies import require_admin
from models.subuser import SubUser
from models.user import User

router = APIRouter(
    prefix="/admin/subusers",
    tags=["Admin - Subusers"],
    dependencies=[Depends(require_admin)]
)

class SubUserSchema(BaseModel):
    id: uuid.UUID
    enterprise_user_id: uuid.UUID
    external_user_id: str
    status: str
    display_name: str | None = None
    last_request_at: Any | None = None
    last_request_ip: str | None = None
    request_count: int
    meta: Dict[str, Any] | None = None
    
    class Config:
        from_attributes = True

class SubUserUpdateStatus(BaseModel):
    status: str

@router.get("/", response_model=List[SubUserSchema])
async def list_subusers(
    db: AsyncSession = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100,
    enterprise_user_id: Optional[uuid.UUID] = Query(None, description="Filter by enterprise user"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    List all subusers in the system. Admins only.
    """
    query = select(SubUser)
    
    if enterprise_user_id:
        query = query.where(SubUser.enterprise_user_id == enterprise_user_id)
    if status:
        query = query.where(SubUser.status == status)
        
    query = query.offset(skip).limit(limit).order_by(SubUser.created_at.desc())
    
    result = await db.execute(query)
    subusers = result.scalars().all()
    return subusers

@router.get("/{subuser_id}", response_model=SubUserSchema)
async def get_subuser(
    subuser_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get detailed information for a specific subuser. Admins only.
    """
    subuser = await db.get(SubUser, subuser_id)
    if not subuser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subuser not found")
        
    return subuser

@router.put("/{subuser_id}/status", response_model=SubUserSchema)
async def update_subuser_status(
    subuser_id: uuid.UUID,
    status_update: SubUserUpdateStatus,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update a subuser's status (active/banned). Admins only.
    """
    subuser = await db.get(SubUser, subuser_id)
    if not subuser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subuser not found")
        
    if status_update.status not in ["active", "suspended", "banned"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
        
    subuser.status = status_update.status
    db.add(subuser)
    await db.commit()
    await db.refresh(subuser)
    return subuser

@router.delete("/{subuser_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subuser(
    subuser_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a subuser. Admins only.
    """
    subuser = await db.get(SubUser, subuser_id)
    if not subuser:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subuser not found")
        
    await db.delete(subuser)
    await db.commit()
    return None
