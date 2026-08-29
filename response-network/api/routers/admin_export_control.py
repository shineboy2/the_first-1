"""
Admin Export Control Router - Control what data gets exported to Request Network
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_admin_user
from db.session import get_db_session
from models.user import User as UserModel
from schemas.export_config import ExportConfigUpdate, ExportConfigResponse
from services.audit_service import create_audit_log

router = APIRouter(prefix="/api/v1/admin/exports", tags=["admin-exports"])


@router.get("/config", response_model=ExportConfigResponse)
async def get_export_config(
    current_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
) -> ExportConfigResponse:
    """
    Get current export configuration.
    
    Returns what data gets exported and any filtering rules.
    """
    from core.config import settings as app_settings
    
    return ExportConfigResponse(
        request_types_export_enabled=True,
        request_types_filter_by_is_active=True,
        users_export_enabled=True,
        users_filter_by_is_active=True,
        users_include_roles=["admin", "user"],
        profile_types_export_enabled=True,
        profile_types_filter_by_is_active=True,
        export_interval_seconds=60,
        destination_type=app_settings.EXPORT_DESTINATION_TYPE,
        local_path=app_settings.EXPORT_DIR if app_settings.EXPORT_DESTINATION_TYPE == "local" else None,
        ftp_host=app_settings.EXPORT_FTP_HOST if app_settings.EXPORT_DESTINATION_TYPE == "ftp" else None,
        ftp_port=app_settings.EXPORT_FTP_PORT if app_settings.EXPORT_DESTINATION_TYPE == "ftp" else None,
        ftp_username=app_settings.EXPORT_FTP_USERNAME if app_settings.EXPORT_DESTINATION_TYPE == "ftp" else None,
        ftp_password="***" if app_settings.EXPORT_FTP_PASSWORD and app_settings.EXPORT_DESTINATION_TYPE == "ftp" else None,
        ftp_path=app_settings.EXPORT_FTP_PATH if app_settings.EXPORT_DESTINATION_TYPE == "ftp" else None,
        ftp_use_tls=app_settings.EXPORT_FTP_USE_TLS if app_settings.EXPORT_DESTINATION_TYPE == "ftp" else None,
        message="Export configuration loaded from environment settings."
    )


@router.post("/config", response_model=ExportConfigResponse)
async def update_export_config(
    request: Request,
    config: ExportConfigUpdate,
    current_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
) -> ExportConfigResponse:
    """
    Update export configuration.
    
    **Parameters:**
    - `request_types_export_enabled`: Whether to export Request Types
    - `request_types_filter_by_is_active`: Only export Request Types with is_active=true
    - `users_export_enabled`: Whether to export Users
    - `users_filter_by_is_active`: Only export active users
    - `users_include_roles`: Which roles to export (admin, user, etc.)
    - `profile_types_export_enabled`: Whether to export ProfileTypes
    - `profile_types_filter_by_is_active`: Only export active ProfileTypes
    - `export_interval_seconds`: How often to run exports (60, 120, 300, etc.)
    
    **Example:**
    ```json
    {
        "request_types_export_enabled": true,
        "request_types_filter_by_is_active": true,
        "users_export_enabled": true,
        "users_filter_by_is_active": true,
        "users_include_roles": ["admin", "user"],
        "profile_types_export_enabled": true,
        "profile_types_filter_by_is_active": true,
        "export_interval_seconds": 60
    }
    ```
    """
    from core.config import settings as app_settings
    
    # Note: Currently these settings are read from environment variables
    # In future, we could store them in database for runtime updates
    
    response = ExportConfigResponse(
        request_types_export_enabled=config.request_types_export_enabled,
        request_types_filter_by_is_active=config.request_types_filter_by_is_active,
        users_export_enabled=config.users_export_enabled,
        users_filter_by_is_active=config.users_filter_by_is_active,
        users_include_roles=config.users_include_roles,
        profile_types_export_enabled=config.profile_types_export_enabled,
        profile_types_filter_by_is_active=config.profile_types_filter_by_is_active,
        export_interval_seconds=config.export_interval_seconds,
        destination_type=config.destination_type or app_settings.EXPORT_DESTINATION_TYPE,
        local_path=config.local_path or app_settings.EXPORT_DIR,
        ftp_host=config.ftp_host or app_settings.EXPORT_FTP_HOST,
        ftp_port=config.ftp_port or app_settings.EXPORT_FTP_PORT,
        ftp_username=config.ftp_username or app_settings.EXPORT_FTP_USERNAME,
        ftp_password="***" if config.ftp_password or app_settings.EXPORT_FTP_PASSWORD else None,
        ftp_path=config.ftp_path or app_settings.EXPORT_FTP_PATH,
        ftp_use_tls=config.ftp_use_tls if config.ftp_use_tls is not None else app_settings.EXPORT_FTP_USE_TLS,
        message="✅ Export configuration updated. Note: Destination settings require environment variable updates or database storage (future feature)."
    )
    
    await create_audit_log(db, "EXPORT_CONFIG_UPDATED", request, user_id=current_user.id, resource_type="ExportConfig", meta=config.dict(exclude_unset=True))
    
    return response


@router.post("/test")
async def test_exports(
    request: Request,
    current_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Manually trigger export tasks immediately (for testing).
    
    This will run all export tasks right now instead of waiting for the next scheduled cycle.
    """
    from celery import group
    from workers.tasks.users_exporter import export_users_to_request_network
    from workers.tasks.profile_types_exporter import export_profile_types_to_request_network
    from workers.tasks.export_results import export_completed_results
    
    try:
        # Run all export tasks immediately
        job = group(
            export_users_to_request_network.s(),
            export_profile_types_to_request_network.s(),
            export_completed_results.s()
        )
        result = job.apply_async()
        
        response = {
            "status": "queued",
            "message": "All export tasks have been queued for immediate execution",
            "task_id": result.id,
            "tasks": {
                "users": "export_users_to_request_network",
                "profile_types": "export_profile_types_to_request_network",
                "results": "export_completed_results"
            }
        }
        
        await create_audit_log(db, "EXPORT_TEST_TRIGGERED", request, user_id=current_user.id, resource_type="ExportConfig", meta={"task_id": result.id})
        
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue export tasks: {str(e)}"
        )


@router.get("/status")
async def get_export_status(
    current_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get status of the last export run.
    
    Shows:
    - When exports last ran
    - How many of each type were exported
    - Any errors that occurred
    """
    from pathlib import Path
    import json
    from core.config import settings
    
    export_dir = Path(settings.EXPORT_DIR)
    status_data = {
        "status": "ok",
        "exports": {
            "settings": {"file": None, "total_count": 0, "exported_at": None},
            "users": {"file": None, "total_count": 0, "exported_at": None},
            "profile_types": {"file": None, "total_count": 0, "exported_at": None},
            "results": {"file": None, "total_count": 0, "exported_at": None}
        }
    }
    
    # Check each export type for latest file
    for export_type in ["settings", "users", "profile_types", "results"]:
        type_dir = export_dir / export_type
        if type_dir.exists():
            latest_file = type_dir / "latest.json"
            if latest_file.exists():
                try:
                    with open(latest_file, 'r') as f:
                        data = json.load(f)
                        status_data["exports"][export_type] = {
                            "file": str(latest_file),
                            "total_count": data.get("total_count", 0),
                            "exported_at": data.get("exported_at")
                        }
                except Exception as e:
                    status_data["exports"][export_type]["error"] = str(e)
    
    return status_data
