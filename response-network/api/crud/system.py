import psutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import redis.asyncio as redis

from models.pydantic_schemas import SystemStats, SystemHealth, LogEntry
from models.request import Request
from workers.elasticsearch_client import ElasticsearchClient
from core.config import settings

async def get_system_stats(db: AsyncSession) -> SystemStats:
    """Get current system resource usage and performance metrics."""
    # Get system resource usage
    cpu_usage = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Calculate requests per minute
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    result = await db.execute(
        select(func.count(Request.id))
        .where(Request.created_at >= one_minute_ago)
    )
    requests_last_minute = result.scalar() or 0
    
    # Calculate average response time for completed requests in last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    result = await db.execute(
        select(func.avg(Request.processing_time))
        .where(
            Request.status == "completed",
            Request.created_at >= one_hour_ago
        )
    )
    avg_response_time = result.scalar() or 0.0

    return SystemStats(
        cpu_usage=cpu_usage,
        memory_usage=memory.percent,
        disk_usage=disk.percent,
        requests_per_minute=float(requests_last_minute),
        avg_response_time=float(avg_response_time)
    )

async def get_system_health(db: AsyncSession, detailed: bool = False) -> SystemHealth:
    """
    Check health status of all system components.
    
    Args:
        db: Database session
        detailed: If True, includes sensitive information like connection details
                 and internal metrics. Default is False for basic health check.
    """
    components = {}
    
    # Check PostgreSQL
    try:
        # Basic connectivity check
        result = await db.execute(select(1))
        result.scalar()
        
        components["database"] = "healthy"
        components["database_stats"] = {"status": "healthy"}
        
    except Exception as e:
        components["database"] = "down"
        logging.error(f"Database health check failed: {str(e)}")
        components["database_stats"] = {"error": str(e)}
    
    # Check Elasticsearch
    try:
        es_client = ElasticsearchClient()
        if await es_client.check_health():
            components["elasticsearch"] = "healthy"
        else:
            components["elasticsearch"] = "degraded"
        await es_client.close_connection()
    except Exception as e:
        components["elasticsearch"] = "down"
        logging.error(f"Elasticsearch health check failed: {str(e)}")
        components["elasticsearch_error"] = str(e)
    
    # Check Redis
    try:
        # Redis connection string سے براہ راست بنائیں
        redis_client = await redis.from_url(str(settings.REDIS_URL))
        await redis_client.ping()
        components["redis"] = "healthy"
        await redis_client.close()
    except Exception as e:
        components["redis"] = "down"
        logging.error(f"Redis health check failed: {str(e)}")
        components["redis_error"] = str(e)
    
    # If not detailed, remove sensitive information
    if not detailed:
        if "database_stats" in components:
            # Keep only essential info for basic health check
            components["database_stats"] = {
                "status": components["database"]
            }
    
    # Determine overall status
    if "down" in components.values():
        status = "down"
    elif "degraded" in components.values():
        status = "degraded"
    else:
        status = "healthy"
    
    # Collect all components stats
    components_stats = {}
    if "database_stats" in components:
        components_stats["database"] = components.pop("database_stats")
    
    return SystemHealth(
        status=status,
        components=components,
        components_stats=components_stats,
        last_check=datetime.utcnow()
    )

async def get_logs(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    level: Optional[str] = None,
    limit: int = 100
) -> List[LogEntry]:
    """Get system logs from the logging system."""
    # This is a placeholder. In a real system, you would:
    # 1. Either query logs from a logging database (e.g., Elasticsearch)
    # 2. Or read and parse log files
    # 3. Or use a logging service API
    
    # For now, we'll return an empty list
    # TODO: Implement actual log retrieval
    return []