from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case
from typing import List, Optional

from core.dependencies import get_db_sync
from auth.dependencies import get_current_user
from models.user import User
from models.request import Request
from core.config import settings
from pathlib import Path
import json

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
    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    active_users = db.scalar(select(func.count()).select_from(User).where(User.is_active == True)) or 0

    # Count total requests
    total_requests = db.scalar(select(func.count()).select_from(Request)) or 0

    # Count requests by status
    processing_requests = db.scalar(select(func.count()).select_from(Request).where(Request.status.in_(["processing", "pending", "exported"]))) or 0
    completed_requests = db.scalar(select(func.count()).select_from(Request).where(Request.status.in_(["completed", "completed_success", "completed_partial"]))) or 0
    failed_requests = db.scalar(select(func.count()).select_from(Request).where(Request.status.in_(["failed", "completed_failed"]))) or 0

    # Get requests by type
    requests_by_type_query = select(Request.query_type.label("type"), func.count(Request.id).label("count")).group_by(Request.query_type)
    requests_by_type_result = db.execute(requests_by_type_query)
    requests_by_type = [{"type": row.type, "count": row.count} for row in requests_by_type_result.all()]

    # Get user request stats
    user_request_stats_query = select(
        User.username.label("username"),
        func.count(Request.id).label("total"),
        func.sum(case((Request.status.in_(["completed", "completed_success", "completed_partial"]), 1), else_=0)).label("completed")
    ).outerjoin(Request).group_by(User.id)
    user_request_stats_result = db.execute(user_request_stats_query)
    user_request_stats = [
        {"username": row.username, "total": row.total, "completed": row.completed or 0} 
        for row in user_request_stats_result.all() if row.total > 0
    ]

    # Get request types active/inactive from filesystem
    active_types = 0
    inactive_types = 0
    import_base = Path(settings.IMPORT_DIR)
    request_types_path = import_base / "request_types" / "latest.json"
    if request_types_path.exists():
        try:
            with open(request_types_path, "r") as f:
                data = json.load(f)
                for item in data:
                    if item.get("is_active", False):
                        active_types += 1
                    else:
                        inactive_types += 1
        except Exception:
            pass

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
        "requests_by_type": requests_by_type,
        "user_request_stats": user_request_stats,
        "request_types_stats": { "active": active_types, "inactive": inactive_types },
        "total_export_batches": 0,
        "total_import_batches": 0
    }
