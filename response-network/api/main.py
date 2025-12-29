import logging
import sys
import os
from pathlib import Path
from typing import Annotated
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import redis
from fastapi import Depends, FastAPI, HTTPException, status, Response
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer

# Import core modules
from core.config import settings
from db.session import get_db_session, async_session
from router import request_router, system_router, user_router, monitoring_router, stats_router
from router import auth_router, request_type_router, worker_settings, profile_type_router, settings_router
from routers import admin_tasks
from routers import admin_export_control
from routers import admin_panel
from routers import profile_type_access

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Monitoring and Admin API for the isolated Response Network.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "system", "description": "System health endpoints"},
        {"name": "monitoring", "description": "Monitoring and statistics endpoints"},
        {"name": "auth", "description": "Authentication operations"},
        {"name": "users", "description": "User management operations"},
        {"name": "requests", "description": "Request handling endpoints"},
        {"name": "request-types", "description": "Manage request types and their parameters"},
        {"name": "profile types", "description": "User profile types management"}
    ]
)

# Configure Security
from auth.dependencies import oauth2_scheme

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
        "*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Content-Length"],
)


# Include routers with security scheme
app.include_router(
    request_router, 
    prefix=settings.API_V1_STR,
    dependencies=[Depends(oauth2_scheme)]
)
app.include_router(
    system_router, 
    prefix=settings.API_V1_STR
)
app.include_router(
    user_router, 
    prefix=settings.API_V1_STR,
    dependencies=[Depends(oauth2_scheme)]
)
app.include_router(
    monitoring_router,
    prefix=settings.API_V1_STR
)
app.include_router(
    stats_router,
    prefix=settings.API_V1_STR,
    dependencies=[Depends(oauth2_scheme)]
)
app.include_router(
    request_type_router,
    prefix=settings.API_V1_STR,
    dependencies=[Depends(oauth2_scheme)]
)
# Auth router doesn't need the security scheme as it contains the login endpoint
app.include_router(auth_router, prefix=settings.API_V1_STR)

# Also register auth endpoints at root level for frontend compatibility
# We'll add a simple redirect/proxy endpoint

# Worker settings router
app.include_router(worker_settings.router, prefix=settings.API_V1_STR)

# Settings router
app.include_router(settings_router, prefix=settings.API_V1_STR, dependencies=[Depends(oauth2_scheme)])

# Profile types router
app.include_router(profile_type_router.router, prefix=settings.API_V1_STR, dependencies=[Depends(oauth2_scheme)])

# Admin tasks router (task queue management)
app.include_router(admin_tasks.router, prefix=settings.API_V1_STR, dependencies=[Depends(oauth2_scheme)])

# Admin export control router
app.include_router(admin_export_control.router, dependencies=[Depends(oauth2_scheme)])

# Admin panel monitoring router
app.include_router(admin_panel.router, dependencies=[Depends(oauth2_scheme)])

# Profile Type Access router
app.include_router(profile_type_access.router, prefix=settings.API_V1_STR, dependencies=[Depends(oauth2_scheme)])


# Auth endpoints are now properly routed through auth_router at /api/v1/auth/


@app.on_event("startup")
async def startup_event():
    logger.info("Monitoring API startup...")
    try:
        # Test database connection
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            logger.info("Database connection successful")
    except Exception as e:
        logger.warning(f"Database connection not available on startup: {str(e)}")
        # Don't raise - allow app to start anyway
async def detailed_health_check(db: AsyncSession = Depends(get_db_session)):
    """
    Performs a detailed health check on critical services.
    """
    health_status = {
        "database": "disconnected",
        "redis_broker": "disconnected",
    }
    # Check Database
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    # Check Redis
    try:
        redis_client = redis.from_url(str(settings.REDIS_URL))
        if redis_client.ping():
            health_status["redis_broker"] = "ok"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")

    return health_status

@app.get(f"{settings.API_V1_STR}/stats/queues", tags=["monitoring"], dependencies=[Depends(oauth2_scheme)])
async def queue_stats():
    """
    Gets the length of the main Celery task queues.
    """
    try:
        redis_client = redis.from_url(str(settings.REDIS_URL))
        # Celery's default queue is named 'celery'
        default_queue_length = redis_client.llen("celery")
        # Celery creates other internal queues, we can monitor them too if needed.
        return {
            "default_queue_length": default_queue_length,
            "notes": "This shows pending tasks in the default queue.",
        }
    except Exception as e:
        logger.error(f"Could not get queue stats: {e}")
        raise HTTPException(status_code=500, detail="Could not connect to Redis to get queue stats.")

@app.get(f"{settings.API_V1_STR}/stats/workers", tags=["monitoring"], dependencies=[Depends(oauth2_scheme)])
async def worker_stats():
    """
    Gets a list of active (online) Celery workers by pinging them.
    """
    try:
        # Currently disabled - will be implemented later
        return {
            "status": "disabled",
            "message": "Worker stats endpoint is temporarily disabled"
        }

        if active_workers is None:
            # This can happen if the broker is down or no workers are connected.
            return {"active_workers": [], "count": 0, "status": "No workers responded. Broker might be down or no workers are running."}

        return {
            "active_workers": list(active_workers.keys()),
            "count": len(active_workers),
        }
    except Exception as e:
        logger.error(f"Could not get worker stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not inspect Celery workers: {e}")

@app.get(f"{settings.API_V1_STR}/stats/cache", tags=["monitoring"], dependencies=[Depends(oauth2_scheme)])
async def cache_stats():
    """
    Gets statistics about the Redis cache, including memory usage and hit/miss ratio.
    """
    try:
        # Use decode_responses=True to get strings instead of bytes
        redis_client = redis.from_url(str(settings.REDIS_URL), decode_responses=True)
        info = redis_client.info()

        hits = int(info.get("keyspace_hits", 0))
        misses = int(info.get("keyspace_misses", 0))
        total_lookups = hits + misses

        cache_metrics = {
            "memory": {
                "used_memory_human": info.get("used_memory_human"),
                "peak_memory_human": info.get("used_memory_peak_human"),
                "max_memory_human": info.get("maxmemory_human", "N/A"),
                "fragmentation_ratio": info.get("mem_fragmentation_ratio"),
                "eviction_policy": info.get("maxmemory_policy"),
            },
            "stats": {
                "total_keys": redis_client.dbsize(),
                "keyspace_hits": hits,
                "keyspace_misses": misses,
                "hit_ratio": f"{(hits / total_lookups * 100):.2f}%" if total_lookups > 0 else "N/A",
            },
            "clients": {
                "connected_clients": info.get("connected_clients"),
            },
        }

        return cache_metrics

    except redis.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to Redis for cache stats: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to Redis.")