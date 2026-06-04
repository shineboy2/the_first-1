"""
Admin Panel Monitoring API for Response Network
مانیتورینگ و کنترل از دور توسط Admin Panel
"""

import logging
from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text, case
from sqlalchemy.ext.asyncio import AsyncSession
import redis
import redis.asyncio

from core.config import settings
from db.session import get_db_session
from models.user import User
from models.incoming_request import IncomingRequest
from models.query_result import QueryResult
from models.sync_history import SyncHistory
from auth.dependencies import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Admin Panel"],
)


# ============================================================================
# SYSTEM HEALTH ENDPOINTS
# ============================================================================


@router.get("/health")
async def admin_health_check(
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    General health check for admin panel
    """
    health = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check Database
    try:
        await db.execute(text("SELECT 1"))
        health["services"]["database"] = "✅ online"
    except Exception as e:
        health["services"]["database"] = f"❌ offline: {str(e)}"
        health["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client = redis.from_url(str(settings.REDIS_URL))
        redis_client.ping()
        health["services"]["redis"] = "✅ online"
    except Exception as e:
        health["services"]["redis"] = f"❌ offline: {str(e)}"
        health["status"] = "degraded"
    
    # Check Elasticsearch (optional)
    try:
        from services.elasticsearch_client import get_elasticsearch_client
        es = get_elasticsearch_client()
        cluster_info = es.info()
        health["services"]["elasticsearch"] = "✅ online"
    except Exception as e:
        health["services"]["elasticsearch"] = f"⚠️ warning: {str(e)}"
    
    return health


@router.get("/health/detailed")
async def admin_health_detailed(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[None, Depends(get_current_admin_user)] = None,
):
    """
    Detailed health check with service metrics
    """
    health = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": {},
        "redis": {},
        "elasticsearch": {},
    }
    
    # Database metrics
    try:
        result = await db.execute(text("SELECT version()"))
        version = result.scalar()
        
        # Connection pool stats
        result = await db.execute(text("""
            SELECT count(*) as connections 
            FROM pg_stat_activity 
            WHERE datname = current_database()
        """))
        conn_count = result.scalar()
        
        health["database"] = {
            "status": "✅ online",
            "version": version,
            "active_connections": conn_count,
        }
    except Exception as e:
        health["database"] = {"status": "❌ offline", "error": str(e)}
    
    # Redis metrics
    try:
        redis_client = redis.from_url(str(settings.REDIS_URL), decode_responses=True)
        info = redis_client.info()
        
        health["redis"] = {
            "status": "✅ online",
            "used_memory": info.get("used_memory_human", "N/A"),
            "peak_memory": info.get("used_memory_peak_human", "N/A"),
            "connected_clients": info.get("connected_clients", 0),
            "total_commands": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
        }
    except Exception as e:
        health["redis"] = {"status": "❌ offline", "error": str(e)}
    
    # Elasticsearch metrics
    try:
        from services.elasticsearch_client import get_elasticsearch_client
        es = get_elasticsearch_client()
        info = es.info()
        
        health["elasticsearch"] = {
            "status": "✅ online",
            "version": info.get("version", {}).get("number", "N/A"),
            "cluster_name": info.get("cluster_name", "N/A"),
        }
    except Exception as e:
        health["elasticsearch"] = {"status": "⚠️ offline", "error": str(e)}
    
    return health


# ============================================================================
# SYSTEM STATISTICS
# ============================================================================


@router.get("/stats/system")
async def get_system_stats(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[None, Depends(get_current_admin_user)] = None,
):
    """
    Get overall system statistics
    """
    try:
        # User statistics
        total_users = await db.scalar(select(func.count(User.id)))
        active_users = await db.scalar(
            select(func.count(User.id)).where(User.is_active == True)
        )
        
        # Request statistics
        total_requests = await db.scalar(select(func.count(IncomingRequest.id)))
        processing = await db.scalar(
            select(func.count(IncomingRequest.id)).where(IncomingRequest.status == "processing")
        )
        completed = await db.scalar(
            select(func.count(IncomingRequest.id)).where(IncomingRequest.status == "completed")
        )
        failed = await db.scalar(
            select(func.count(IncomingRequest.id)).where(IncomingRequest.status == "failed")
        )
        
        # Query result statistics
        total_results = await db.scalar(select(func.count(QueryResult.id)))
        
        # Database size
        result = await db.execute(text("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as size
        """))
        db_size = result.scalar()
        
        # New detailed stats for Dashboard Charts
        from models.external_api import ExternalAPI
        
        # Requests by Type
        requests_by_type_stmt = select(
            IncomingRequest.query_type.label("type"),
            func.count(IncomingRequest.id).label("count")
        ).group_by(IncomingRequest.query_type)
        requests_by_type_result = await db.execute(requests_by_type_stmt)
        requests_by_type = [{"type": row.type, "count": row.count} for row in requests_by_type_result.all()]
        
        # User Request Stats
        user_request_stats_stmt = select(
            User.username.label("username"),
            func.count(IncomingRequest.id).label("total"),
            func.sum(case((IncomingRequest.status == 'completed', 1), else_=0)).label("completed")
        ).outerjoin(IncomingRequest, User.id == IncomingRequest.user_id).group_by(User.id)
        user_request_stats_result = await db.execute(user_request_stats_stmt)
        user_request_stats = [
            {"username": row.username, "total": row.total, "completed": row.completed or 0} 
            for row in user_request_stats_result.all() if row.total > 0
        ]
        
        # Request Types Stats
        active_types = await db.scalar(select(func.count(ExternalAPI.id)).where(ExternalAPI.is_active == True))
        inactive_types = await db.scalar(select(func.count(ExternalAPI.id)).where(ExternalAPI.is_active == False))

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "users": {
                "total": total_users,
                "active": active_users,
            },
            "requests": {
                "total": total_requests,
                "processing": processing,
                "completed": completed,
                "failed": failed,
            },
            "results": {
                "total": total_results,
            },
            "database": {
                "size": db_size,
            },
            "requests_by_type": requests_by_type,
            "user_request_stats": user_request_stats,
            "request_types_stats": {
                "active": active_types or 0,
                "inactive": inactive_types or 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving system statistics")


# ============================================================================
# QUEUE MONITORING
# ============================================================================


@router.get("/stats/queues")
async def get_queue_stats(
    _: Annotated[None, Depends(get_current_admin_user)] = None,
):
    """
    Get Celery task queue statistics
    """
    try:
        redis_client = redis.from_url(str(settings.REDIS_URL))
        
        queue_lengths = {
            "default": redis_client.llen("celery"),
            "high": redis_client.llen("high"),
            "medium": redis_client.llen("medium"),
            "low": redis_client.llen("low"),
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "queues": queue_lengths,
            "total_pending": sum(queue_lengths.values()),
        }
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving queue statistics")


# ============================================================================
# USER MANAGEMENT
# ============================================================================


@router.get("/users/list")
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = 0,
    limit: int = 100,
    _: Annotated[None, Depends(get_current_admin_user)] = None,
):
    """
    List all users with pagination
    """
    try:
        users = await db.execute(
            select(User).offset(skip).limit(limit)
        )
        users_list = users.scalars().all()
        
        total = await db.scalar(select(func.count(User.id)))
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "users": [
                {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                }
                for user in users_list
            ],
        }
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving users")


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[None, Depends(get_current_admin_user)] = None,
):
    """
    Get detailed information about a specific user
    """
    try:
        from uuid import UUID
        
        user = await db.get(User, UUID(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # User statistics
        total_requests = await db.scalar(
            select(func.count(IncomingRequest.id)).where(
                IncomingRequest.user_id == user.id
            )
        )
        
        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "statistics": {
                "total_requests": total_requests,
            },
        }
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving user details")


# ============================================================================
# REQUEST MONITORING
# ============================================================================


@router.get("/requests/recent")
async def get_recent_requests(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = 20,
    _: Annotated[None, Depends(get_current_admin_user)] = None,
):
    """
    Get recent requests with their status
    """
    try:
        requests = await db.execute(
            select(IncomingRequest)
            .order_by(IncomingRequest.created_at.desc())
            .limit(limit)
        )
        reqs = requests.scalars().all()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(reqs),
            "requests": [
                {
                    "id": str(req.id),
                    "user_id": str(req.user_id),
                    "status": req.status,
                    "created_at": req.created_at.isoformat() if req.created_at else None,
                    "completed_at": req.completed_at.isoformat() if req.completed_at else None,
                }
                for req in reqs
            ],
        }
    except Exception as e:
        logger.error(f"Error getting recent requests: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving requests")


@router.get("/requests/stats")
async def get_request_stats(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[None, Depends(get_current_admin_user)] = None,
):
    """
    Get request statistics by status
    """
    try:
        pending = await db.scalar(
            select(func.count(IncomingRequest.id)).where(IncomingRequest.status == "pending")
        )
        processing = await db.scalar(
            select(func.count(IncomingRequest.id)).where(IncomingRequest.status == "processing")
        )
        completed = await db.scalar(
            select(func.count(IncomingRequest.id)).where(IncomingRequest.status == "completed")
        )
        failed = await db.scalar(
            select(func.count(IncomingRequest.id)).where(IncomingRequest.status == "failed")
        )
        
        total = pending + processing + completed + failed
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total": total,
            "by_status": {
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
            },
            "percentages": {
                "pending": f"{(pending/total*100):.1f}%" if total > 0 else "0%",
                "processing": f"{(processing/total*100):.1f}%" if total > 0 else "0%",
                "completed": f"{(completed/total*100):.1f}%" if total > 0 else "0%",
                "failed": f"{(failed/total*100):.1f}%" if total > 0 else "0%",
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving request statistics")

from pydantic import BaseModel
class ScheduleUpdate(BaseModel):
    interval: float

@router.get("/celery/schedules")
async def get_celery_schedules(
    _: Annotated[None, Depends(get_current_admin_user)] = None
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
            "enabled": True
        })
    return schedules

@router.put("/celery/schedules/{name}")
async def update_celery_schedule(
    name: str,
    update_data: ScheduleUpdate,
    _: Annotated[None, Depends(get_current_admin_user)] = None
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

@router.get("/sync-status")
async def get_sync_status(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[None, Depends(get_current_admin_user)] = None,
):
    """
    Get the latest sync status for various operation types.
    """
    try:
        # Get the latest sync history for each operation type
        operations = ["user_export", "request_types_export", "result_export", "request_import"]
        results = {}
        for op in operations:
            stmt = select(SyncHistory).where(SyncHistory.operation_type == op).order_by(SyncHistory.started_at.desc()).limit(1)
            result = await db.execute(stmt)
            history = result.scalar_one_or_none()
            if history:
                results[op] = {
                    "status": history.status,
                    "started_at": history.started_at.isoformat() if history.started_at else None,
                    "completed_at": history.completed_at.isoformat() if history.completed_at else None,
                    "details": history.details,
                }
            else:
                results[op] = None
        
        return results
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving sync status")


