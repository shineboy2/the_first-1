from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import func, and_, select
from sqlalchemy.sql import Select

from models.request import Request
from models.query_result import QueryResult
from models.pydantic_schemas import (
    RequestStats,
    QueryStats,
    SystemHealth,
    SystemStats,
    LogEntry
)

async def get_request_stats(
    db: AsyncSession,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> RequestStats:
    """Get statistics about requests processed by the response network."""
    query = select(Request)
    
    if start_date:
        start = datetime.fromisoformat(start_date)
        query = query.where(Request.created_at >= start)
    if end_date:
        end = datetime.fromisoformat(end_date)
        query = query.where(Request.created_at <= end)

    result = await db.execute(query)
    requests = result.scalars().all()
    
    total_count = len(requests)
    successful = sum(1 for r in requests if r.status == "completed")
    failed = sum(1 for r in requests if r.status == "failed")
    
    avg_query = select(func.avg(QueryResult.execution_time_ms)).where(
        QueryResult.request_id.in_([r.id for r in requests])
    )
    avg_result = await db.execute(avg_query)
    avg_response_time = float(avg_result.scalar() or 0) / 1000.0  # Convert ms to seconds

    return RequestStats(
        total_count=total_count,
        successful_count=successful,
        failed_count=failed,
        average_response_time=float(avg_response_time)
    )

async def get_query_stats(
    db: AsyncSession,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> QueryStats:
    """Get statistics about queries processed by the response network."""
    # Similar implementation as request stats but for queries
    # This will be implemented when the Query model is finalized
    return QueryStats(
        total_count=0,
        successful_count=0,
        failed_count=0,
        average_processing_time=0.0
    )

async def get_system_health(db: AsyncSession) -> SystemHealth:
    """Get current system health status."""
    # Check various system components and return health status
    # This will integrate with monitoring tools/services
    return SystemHealth(
        status="healthy",
        components={
            "database": "healthy",
            "cache": "healthy",
            "search": "healthy"
        },
        last_check=datetime.now(timezone.utc)
    )

async def get_system_stats(
    db: AsyncSession,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> SystemStats:
    """Get system performance statistics."""
    # Collect system performance metrics
    # This will integrate with monitoring tools/services
    return SystemStats(
        cpu_usage=0.0,
        memory_usage=0.0,
        disk_usage=0.0,
        requests_per_minute=0.0,
        avg_response_time=0.0
    )

async def get_logs(
    db: AsyncSession,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[LogEntry]:
    """Get system logs with filtering options."""
    # Implement log retrieval from logging system
    # This will integrate with logging service
    return []