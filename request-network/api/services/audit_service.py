import uuid
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from models.audit_log import AuditLog

async def create_audit_log(
    db: AsyncSession,
    action: str,
    request: Request,
    user_id: Optional[uuid.UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    request_data: Optional[Dict[str, Any]] = None,
    response_status: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
    commit: bool = True
) -> AuditLog:
    """
    Creates an audit log entry in the database.
    """
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        ip_address=ip_address,
        user_agent=user_agent,
        request_data=request_data,
        response_status=response_status,
        meta=meta
    )
    
    db.add(audit_log)
    
    if commit:
        await db.commit()
    
    return audit_log
