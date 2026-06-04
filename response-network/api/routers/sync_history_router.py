from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from auth.dependencies import get_current_admin_user
from db.session import get_db_session
from models.sync_history import SyncHistory
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

router = APIRouter(prefix="/admin/sync-history", tags=["sync-history"])

class SyncHistoryResponse(BaseModel):
    id: UUID
    operation_type: str
    status: str
    details: Optional[dict] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[SyncHistoryResponse])
async def get_sync_history(
    limit: int = 50,
    operation_type: Optional[str] = None,
    current_user = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    query = select(SyncHistory).order_by(desc(SyncHistory.started_at))
    if operation_type:
        query = query.where(SyncHistory.operation_type == operation_type)
    
    query = query.limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()
    return records
