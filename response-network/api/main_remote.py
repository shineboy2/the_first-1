from fastapi.staticfiles import StaticFiles
import logging
import sys
import os
from pathlib import Path
from typing import Annotated
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import redis
from fastapi import Depends, FastAPI, HTTPException, status, Response
from fastapi.openapi.utils import get_openapi
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer

# Import core modules
from core.config import settings
from db.session import get_db_session, async_session
from routers import request_router, system_router, user_router, monitoring_router, stats_router
from routers import auth_router, request_type_router, worker_settings, profile_type_router, settings_router, admin_exports, storage_config_router
from routers import external_apis
from routers import elasticsearch_config
from routers import captcha_router
from routers import sync_history_router
from routers import admin_panel
from routers import profile_type_access
from custom_swagger import get_swagger_ui_html

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Monitoring and Admin API for the isolated Response Network.",
    version="0.1.0",
    docs_url=None,  # Disable default Swagger
    redoc_url=None,
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

# Mount static files for offline Swagger UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Security
from auth.dependencies import oauth2_scheme

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
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

# Also register# Auth endpoints are now properly routed through auth_router at /api/v1/auth/
app.include_router(captcha_router.router, prefix=settings.API_V1_STR)
app.include_router(sync_history_router.router, prefix=settings.API_V1_STR)
# We'll add a simple redirect/proxy endpoint

# Worker settings router
app.include_router(worker_settings.router, prefix=settings.API_V1_STR)

# Storage configuration router
app.include_router(storage_config_router.router, prefix=settings.API_V1_STR)

# Settings router
app.include_router(settings_router, prefix=settings.API_V1_STR, dependencies=[Depends(oauth2_scheme)])

# Profile types router
app.include_router(profile_type_router.router, prefix=settings.API_V1_STR, dependencies=[Depends(oauth2_scheme)])

# Admin tasks router (task queue management)
app.include_router(admin_tasks.router, prefix=settings.API_V1_STR, dependencies=[Depends(oauth2_scheme)])

# Admin export control router (DISABLED - replaced by admin_exports)
# app.include_router(admin_export_control.router, dependencies=[Depends(oauth2_scheme)])

# Admin panel monitoring router
app.include_router(admin_panel.router, dependencies=[Depends(oauth2_scheme)])

# Profile Type Access router
app.include_router(profile_type_access.router, prefix=settings.API_V1_STR, dependencies=[Depends(oauth2_scheme)])

# Admin Exports router (for Frontend compatibility)
app.include_router(admin_exports.router, prefix=settings.API_V1_STR, dependencies=[Depends(oauth2_scheme)])

# Custom Swagger UI endpoint (offline)
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title + " - Swagger UI",
    )


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



def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version="3.0.2",
        description=app.description,
        routes=app.routes,
    )
    # Downgrade OpenAPI version if get_openapi still returns 3.1.0 
    # (though explicit argument valid in recent FastAPI)
    if openapi_schema.get("openapi", "").startswith("3.1"):
        openapi_schema["openapi"] = "3.0.2"
        
        # Remove webhooks if present (3.1 feature)
        if "webhooks" in openapi_schema:
            del openapi_schema["webhooks"]
            
        # Ensure components are compatible
        if "components" in openapi_schema:
             # Clean up any constrained types that might use 3.1 syntax (e.g. exclusiveMinimum)
             pass

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
