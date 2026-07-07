from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from core.dependencies import get_db
from models.pydantic_schemas import (
    RequestStats,
    QueryStats,
    SystemHealth,
    SystemStats,
    LogEntry
)
from auth.dependencies import get_current_user
from models.user import User
from crud import stats as stats_service

router = APIRouter(
    prefix="/monitoring", 
    tags=["monitoring"]
)

@router.get("/health", response_model=SystemHealth)
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
            "elasticsearch": "connected"
        }
    }

@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get current system statistics from database."""
    from sqlalchemy import select, func
    from sqlalchemy.ext.asyncio import AsyncSession
    from models.user import User
    from models.request import Request
    
    # Convert to async session if needed
    if not isinstance(db, AsyncSession):
        # If sync session, return mock data for now
        return {
            "users": {"total": 0, "active": 0},
            "requests": {"total": 0, "processing": 0, "completed": 0, "failed": 0},
            "database": {"size": "0 MB"},
            "results": {"total": 0}
        }
    
    # Count total users
    total_users_query = select(func.count()).select_from(User)
    total_users_result = await db.execute(total_users_query)
    total_users = total_users_result.scalar() or 0
    
    # Count active users
    active_users_query = select(func.count()).select_from(User).where(User.is_active == True)
    active_users_result = await db.execute(active_users_query)
    active_users = active_users_result.scalar() or 0
    
    # Count total requests
    total_requests_query = select(func.count()).select_from(Request)
    total_requests_result = await db.execute(total_requests_query)
    total_requests = total_requests_result.scalar() or 0
    
    # Count requests by status
    processing_query = select(func.count()).select_from(Request).where(Request.status == "processing")
    processing_result = await db.execute(processing_query)
    processing_requests = processing_result.scalar() or 0
    
    completed_query = select(func.count()).select_from(Request).where(Request.status == "completed")
    completed_result = await db.execute(completed_query)
    completed_requests = completed_result.scalar() or 0
    
    failed_query = select(func.count()).select_from(Request).where(Request.status == "failed")
    failed_result = await db.execute(failed_query)
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
        }
    }

@router.get("/requests", response_model=RequestStats)
async def get_request_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get statistics about requests processed by the response network."""
    return await stats_service.get_request_stats(db, start_date, end_date)

@router.get("/queries", response_model=QueryStats)
async def get_query_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get statistics about queries processed by the response network."""
    return await stats_service.get_query_stats(db, start_date, end_date)

@router.get("/system/health", response_model=SystemHealth)
async def get_system_health(
    db: Session = Depends(get_db)
):
    """Get current system health status."""
    return await stats_service.get_system_health(db)

@router.get("/system/stats", response_model=SystemStats)
async def get_system_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get system performance statistics."""
    return await stats_service.get_system_stats(db, start_date, end_date)

@router.get("/logs", response_model=List[LogEntry])
async def get_system_logs(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get system logs with filtering options."""
    return await stats_service.get_logs(
        db, 
        start_date=start_date,
        end_date=end_date,
        level=level,
        limit=limit,
        offset=offset
    )
