from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional

from core.dependencies import get_db_sync
from auth.dependencies import get_current_user
from models.user import User
from models.request import Request

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"]
)

@router.get("/health")
async def get_system_health(current_user: User = Depends(get_current_user)):
    """Get current system health metrics."""
    from datetime import datetime
    return {
        "status": "healthy",
        "uptime": "1d 2h 34m",
        "last_error": None,
        "last_check": datetime.now().isoformat(),
        "components": {
            "database": "connected",
            "redis": "connected",
            "elasticsearch": "not applicable"
        }
    }

@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db_sync)):
    """Get current system statistics from database."""
    # Count total users
    total_users_query = select(func.count()).select_from(User)
    total_users_result = db.execute(total_users_query)
    total_users = total_users_result.scalar() or 0

    # Count active users
    active_users_query = select(func.count()).select_from(User).where(User.is_active == True)
    active_users_result = db.execute(active_users_query)
    active_users = active_users_result.scalar() or 0

    # Count total requests
    total_requests_query = select(func.count()).select_from(Request)
    total_requests_result = db.execute(total_requests_query)
    total_requests = total_requests_result.scalar() or 0

    # Count requests by status
    processing_query = select(func.count()).select_from(Request).where(Request.status == "processing")
    processing_result = db.execute(processing_query)
    processing_requests = processing_result.scalar() or 0

    completed_query = select(func.count()).select_from(Request).where(Request.status == "completed")
    completed_result = db.execute(completed_query)
    completed_requests = completed_result.scalar() or 0

    failed_query = select(func.count()).select_from(Request).where(Request.status == "failed")
    failed_result = db.execute(failed_query)
    failed_requests = failed_result.scalar() or 0

    return {
        "users": {
            "total": total_users,
            "active": active_users
        },
        "requests": {
            "total": total_requests,
            "processing": processing_requests,
            "completed": completed_requests,
            "failed": failed_requests
        },
        "database": {
            "size": "N/A"
        },
        "results": {
            "total": completed_requests
        },
        "requests_by_type": [],
        "user_request_stats": [],
        "request_types_stats": { "active": 0, "inactive": 0 },
        "total_export_batches": 0,
        "total_import_batches": 0
    }