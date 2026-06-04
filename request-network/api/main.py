import sys
from pathlib import Path
from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# --- Start of Path Fix ---
# Add project root to the Python path to allow imports from `shared`
api_dir = Path(__file__).resolve().parent
project_root = api_dir.parent

# Insert api_dir FIRST so local modules take precedence
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))
    
if str(project_root) not in sys.path:
    sys.path.insert(1, str(project_root))
# --- End of Path Fix ---

from core.config import settings
from core.middleware import RequestContextMiddleware
from core.rate_limiter import RateLimiter
from core.exceptions import global_exception_handler
from rate_limit_middleware import RateLimitGracePeriodMiddleware
from db.session import get_db_session
from routers import auth_router, request_router, admin_router, settings_router, admin_imports, api_key_router, request_types_router
from routers import users as users_router  # Import users router
from routers import external_request
from routers import captcha_router
from router import monitoring_router
from shared.logger import get_logger
from custom_swagger import get_swagger_ui_html

log = get_logger(__name__, level=settings.LOG_LEVEL)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for submitting and managing requests in the air-gapped system.",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,  # Disable default Swagger
    redoc_url=None
)

# Force OpenAPI 3.0.3 for compatibility with bundled offline Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["openapi"] = "3.0.3"
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Mount static files for offline Swagger UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)

# Add Middlewares
app.add_middleware(RequestContextMiddleware)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Rate Limit Grace Period Middleware
app.add_middleware(RateLimitGracePeriodMiddleware)

# Include API routers
from routers import user_management_router
app.include_router(auth_router.router, prefix=settings.API_V1_STR)
app.include_router(captcha_router.router, prefix=settings.API_V1_STR)
app.include_router(users_router.router, prefix=settings.API_V1_STR)
app.include_router(request_router.router, prefix=settings.API_V1_STR)
app.include_router(admin_router.router, prefix=settings.API_V1_STR)
app.include_router(user_management_router.router, prefix=settings.API_V1_STR)
app.include_router(settings_router.router, prefix=settings.API_V1_STR)
app.include_router(external_request.router, prefix=settings.API_V1_STR)
app.include_router(api_key_router.router, prefix=settings.API_V1_STR)
app.include_router(request_types_router.router, prefix=settings.API_V1_STR)
app.include_router(monitoring_router, prefix=settings.API_V1_STR)

# Admin Imports router
app.include_router(admin_imports.router, prefix=f"{settings.API_V1_STR}/admin/imports", dependencies=[Depends(get_db_session)])

# Custom Swagger UI endpoint (offline)
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
    )


@app.on_event("startup")
async def startup_event():
    log.info("Application startup...", api_version=app.version)

@app.get(f"{settings.API_V1_STR}/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Request Network API"}

@app.get(f"{settings.API_V1_STR}/health", tags=["Monitoring"])
async def health_check():
    return {"status": "ok"}

@app.get(f"{settings.API_V1_STR}/health/ready", tags=["Monitoring"])
async def readiness_check(db: AsyncSession = Depends(get_db_session)):
    """
    Checks if the service is ready to accept traffic (e.g., DB is connected).
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        log.error("Readiness check failed: Database connection error.", error=str(e))
        return {"status": "error", "database": "disconnected"}
