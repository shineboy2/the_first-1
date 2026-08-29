from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from db.session import get_db_session
from models.audit_log import AuditLog
from models.user import User
from auth.dependencies import get_current_user, get_current_admin_user

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("/")
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: str = None,
    action: str = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    List all audit logs in the Response Network.
    This contains the long-term history of all user actions.
    """
    query = select(AuditLog, User.username).outerjoin(User, AuditLog.user_id == User.id).order_by(desc(AuditLog.created_at))
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()
    
    logs = []
    for log, username in rows:
        log_dict = {c.name: getattr(log, c.name) for c in log.__table__.columns}
        # Convert UUID to string for JSON serialization
        if log_dict.get('user_id'):
            log_dict['user_id'] = str(log_dict['user_id'])
        log_dict["username"] = username
        logs.append(log_dict)
    
    # Count total
    count_query = select(AuditLog)
    if user_id:
        count_query = count_query.filter(AuditLog.user_id == user_id)
    if action:
        count_query = count_query.filter(AuditLog.action == action)
        
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all()) # Simple count for now
    
    return {
        "items": logs,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit
    }
