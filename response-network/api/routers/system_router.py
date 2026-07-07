from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from core.dependencies import get_db
from models.pydantic_schemas import SystemStats, SystemHealth, LogEntry
from models.user import User
from auth.dependencies import get_current_user, get_current_admin_user
from crud import system as system_service

router = APIRouter(tags=["system"])

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current system statistics including resource usage and performance metrics.
    """
    return await system_service.get_system_stats(db)

@router.get("/health", dependencies=[])  # Simple health endpoint for Docker healthcheck
async def health_check():
    """
    Simple health check endpoint for Docker healthcheck and monitoring.
    Returns 200 OK if the service is running.
    """
    return {"status": "ok"}

@router.get("/system/health", response_model=SystemHealth, dependencies=[])  # Empty dependencies to override the global security
async def get_system_health(
    db: AsyncSession = Depends(get_db)
):
    """
    Get basic health status of the system. This endpoint is public and does not require authentication.
    Used by monitoring services and load balancers.
    """
    return await system_service.get_system_health(db, detailed=False)

@router.get("/system/health/detailed", response_model=SystemHealth)
async def get_detailed_system_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)  # Only admins can see detailed health
):
    """
    Get detailed health status of all system components including sensitive information.
    Requires authentication and admin privileges.
    """
    return await system_service.get_system_health(db, detailed=True)

@router.get("/system/logs", response_model=List[LogEntry])
async def get_system_logs(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    level: Optional[str] = Query(None, enum=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get system logs with filtering options. Only accessible by admin users.
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(hours=24)
    if not end_date:
        end_date = datetime.utcnow()

    return await system_service.get_logs(
        db,
        start_date=start_date,
        end_date=end_date,
        level=level,
        limit=limit
    )