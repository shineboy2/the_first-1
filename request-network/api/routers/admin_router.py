from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, case, select
from sqlalchemy.ext.asyncio import AsyncSession
import os
import json
from pathlib import Path
from datetime import datetime
from core.config import settings

from auth.dependencies import require_admin
from db.session import get_db_session
from db.redis_client import get_redis_client
from models.user import User
from models.request import Request
from models.batch import ExportBatch, ImportBatch
from schemas.admin import SystemStats
from rate_limiter import RateLimiter

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
    # Remove global dependencies - add them per endpoint instead
)


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)] = None  # Add auth check here
):
    """
    Retrieves overall statistics for the system.
    - User counts (total, active)
    - Request counts by status
    - Batch counts (import/export)
    """
    # 1. Get user stats
    user_stats_stmt = select(
        func.count(User.id).label("total_users"),
        func.sum(case((User.is_active == True, 1), else_=0)).label("active_users")
    )
    user_stats_result = (await db.execute(user_stats_stmt)).one()

    # 2. Get request stats
    request_stats_stmt = select(
        func.count(Request.id).label("total_requests"),
        func.count(case((Request.status == 'pending', 1))).label("pending_requests"),
        func.count(case((Request.status == 'completed', 1))).label("completed_requests"),
        func.count(case((Request.status == 'failed', 1))).label("failed_requests"),
    )
    request_stats_result = (await db.execute(request_stats_stmt)).one()

    # 3. Get batch stats
    export_batch_count = await db.scalar(select(func.count(ExportBatch.id)))
    import_batch_count = await db.scalar(select(func.count(ImportBatch.id)))

    # 4. Get requests by type
    requests_by_type_stmt = select(
        Request.query_type.label("type"),
        func.count(Request.id).label("count")
    ).group_by(Request.query_type)
    requests_by_type_result = await db.execute(requests_by_type_stmt)
    requests_by_type = [{"type": row.type, "count": row.count} for row in requests_by_type_result.all()]

    # 5. Get user request stats
    user_request_stats_stmt = select(
        User.username.label("username"),
        func.count(Request.id).label("total"),
        func.sum(case((Request.status == 'completed', 1), else_=0)).label("completed")
    ).outerjoin(Request).group_by(User.id)
    user_request_stats_result = await db.execute(user_request_stats_stmt)
    user_request_stats = [
        {"username": row.username, "total": row.total, "completed": row.completed or 0} 
        for row in user_request_stats_result.all() if row.total > 0
    ]

    # 6. Get request types active/inactive from filesystem
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

    return SystemStats(
        total_users=user_stats_result.total_users,
        active_users=user_stats_result.active_users,
        total_requests=request_stats_result.total_requests,
        pending_requests=request_stats_result.pending_requests,
        completed_requests=request_stats_result.completed_requests,
        failed_requests=request_stats_result.failed_requests,
        total_export_batches=export_batch_count or 0,
        total_import_batches=import_batch_count or 0,
        requests_by_type=requests_by_type,
        user_request_stats=user_request_stats,
        request_types_stats={"active": active_types, "inactive": inactive_types}
    )


from schemas.request import RequestPublic
from typing import List

@router.get("/requests", response_model=List[RequestPublic])
async def get_all_requests(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    _: Annotated[None, Depends(require_admin)] = None
):
    """
    Retrieve a list of all requests in the system.
    Requires admin privileges.
    """
    from sqlalchemy.orm import selectinload
    query = select(Request).order_by(Request.created_at.desc())
    if user_id:
        try:
            import uuid
            query = query.where(Request.user_id == uuid.UUID(user_id))
        except ValueError:
            pass # Invalid UUID, won't match anything anyway
            
    query = (
        query
        .options(selectinload(Request.response))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    requests = result.scalars().all()
    return requests


# ============================================================================
# RATE LIMITING ENDPOINTS (Grace Period)
# ============================================================================


@router.get("/rate-limit/user/{user_id}/stats")
async def get_user_rate_limit_stats(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)] = None
):
    """
    Get rate limit statistics for a specific user.
    
    Shows:
    - Current usage (minute, hour, day)
    - Percentage of limit used
    - Reset times
    """
    redis_client = await get_redis_client()
    rate_limiter = RateLimiter(redis_client.client)
    
    # Get user profile from database
    user = await db.get(User, user_id)
    profile = user.profile_type if user else "free"
    
    stats = await rate_limiter.get_user_stats(user_id, profile)
    return stats


@router.post("/rate-limit/user/{user_id}/reset")
async def reset_user_rate_limit(
    user_id: str,
    window: str = "all",
    _: Annotated[None, Depends(require_admin)] = None
):
    """
    Reset rate limit counter for a user (admin only).
    
    Args:
        user_id: UUID of the user
        window: Which window to reset (minute, hour, day, all)
        
    Returns:
    - Success message
    - Number of counters reset
    """
    redis_client = await get_redis_client()
    rate_limiter = RateLimiter(redis_client.client)
    
    result = await rate_limiter.reset_user_limit(user_id, window)
    return result


@router.post("/rate-limit/user/{user_id}/custom-limits")
async def set_custom_rate_limits(
    user_id: str,
    minute: int = None,
    hour: int = None,
    day: int = None,
    _: Annotated[None, Depends(require_admin)] = None
):
    """
    Set custom rate limits for a user (admin only).
    
    This overrides the default profile limits.
    
    Args:
        user_id: UUID of the user
        minute: Custom per-minute limit
        hour: Custom per-hour limit
        day: Custom per-day limit
        
    Returns:
    - Success message
    - Applied custom limits
    """
    redis_client = await get_redis_client()
    rate_limiter = RateLimiter(redis_client.client)
    
    result = await rate_limiter.set_custom_limits(user_id, minute, hour, day)
    return result


@router.get("/rate-limit/all")
async def get_all_rate_limits(
    _: Annotated[None, Depends(require_admin)] = None
):
    """
    Get rate limit configuration for all profiles.
    
    Returns:
    - Limits for each profile (free, basic, premium, enterprise)
    - Warning thresholds (80%, 110%)
    - Hard block threshold (100%)
    """
    from rate_limiter import RateLimitConfig
    
    config = RateLimitConfig()
    
    return {
        "limits": config.LIMITS,
        "thresholds": {
            "warning": f"{config.WARNING_THRESHOLD * 100}%",
            "soft_block": f"{config.SOFT_BLOCK_THRESHOLD * 100}%",
            "hard_block": f"{config.HARD_BLOCK_THRESHOLD * 100}%",
        },
        "grace_period_duration": "5 minutes",
    }

@router.get("/sync-status")
async def get_sync_status(
    _: Annotated[None, Depends(require_admin)] = None
):
    """
    Get the last synchronization times for various resources.
    Checks the modification time of import files and metadata files.
    """
    status = {}
    
    # 1. Users Sync (Uses .processed_users metadata)
    # Correct path for shared data
    shared_data_dir = Path(os.getenv("SHARED_DATA_DIR", "/app/shared_data"))
    users_meta_path = shared_data_dir / "users" / ".processed_users"
    if users_meta_path.exists():
        try:
            with open(users_meta_path, "r") as f:
                data = json.load(f)
                status["users"] = {
                    "last_sync": data.get("imported_at"),
                    "count": data.get("imported_count"),
                    "checksum": data.get("checksum")[:8] if data.get("checksum") else None
                }
        except Exception:
            status["users"] = {"error": "Could not read metadata"}
    else:
        status["users"] = {"status": "Never synced"}

    # 2. Settings & Resources Sync (Check latest.json mtime)
    # Using settings.IMPORT_DIR from config
    import_base = Path(settings.IMPORT_DIR)
    
    # Map friendly names to folder names
    resources = {
        "settings": "settings",
        "request_types": "request_types", 
        "profile_types": "profile_types"
    }
    
    for key, folder in resources.items():
        resource_path = import_base / folder / "latest.json"
        if resource_path.exists():
            mtime = datetime.fromtimestamp(resource_path.stat().st_mtime)
            status[key] = {
                "last_received": mtime.isoformat(),
                "file_path": str(resource_path)
            }
        else:
            status[key] = {"status": "No data received"}

    return status

from pydantic import BaseModel
class ScheduleUpdate(BaseModel):
    interval: float

@router.get("/celery/schedules")
async def get_celery_schedules(
    _: Annotated[None, Depends(require_admin)] = None
):
    """
    Get all Celery Beat schedules from RedBeat.
    """
    from redbeat import RedBeatSchedulerEntry
    from workers.celery_app import celery_app
    
    entries = RedBeatSchedulerEntry.get_schedules(app=celery_app)
    schedules = []
    for key, entry in entries.items():
        schedules.append({
            "name": entry.name,
            "task": entry.task,
            "interval": entry.schedule.run_every.total_seconds() if hasattr(entry.schedule, "run_every") else None,
            "enabled": True  # Redbeat removes disabled ones by default if we don't save them
        })
    return schedules

@router.put("/celery/schedules/{name}")
async def update_celery_schedule(
    name: str,
    update_data: ScheduleUpdate,
    _: Annotated[None, Depends(require_admin)] = None
):
    """
    Update a Celery Beat schedule interval.
    """
    from redbeat import RedBeatSchedulerEntry
    from workers.celery_app import celery_app
    from fastapi import HTTPException
    
    entries = RedBeatSchedulerEntry.get_schedules(app=celery_app)
    if name not in entries:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    entry = entries[name]
    from celery.schedules import schedule
    entry.schedule = schedule(run_every=update_data.interval)
    entry.save()
    
    return {"message": "Schedule updated successfully", "name": name, "interval": update_data.interval}