"""
Admin Exports Router - For Frontend Admin Panel compatibility
Provides endpoints to configure export/import settings for all operation types
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any, List

from auth.dependencies import get_current_admin_user
from core.dependencies import get_db as get_db_session
from models.settings import Settings as SettingsModel
from models.user import User

router = APIRouter(prefix="/admin/exports", tags=["admin-exports"])

# Operation types and their settings keys
OPERATION_TYPES = {
    "user_export": "export_config",  # Response Network exports users
    "result_export": "result_export_config",  # Response Network exports results
    "request_import": "request_import_config",  # Response Network imports requests
}


@router.post("/config")
async def update_export_config(
    config: Dict[str, Any],
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update export configuration (backward compatible).
    This endpoint is used by the Admin Panel to save export settings.
    Defaults to user_export operation type.
    """
    return await update_storage_config("user_export", config, db)


@router.post("/config/{operation_type}")
async def update_storage_config_by_type(
    operation_type: str,
    config: Dict[str, Any],
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update storage configuration for specific operation type.
    
    Operation Types:
    - user_export: Export users to FTP (for Request Network)
    - request_import: Import requests from FTP (from Request Network)
    - result_export: Export results to FTP (for Request Network)
    """
    if operation_type not in OPERATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation_type. Must be one of: {', '.join(OPERATION_TYPES.keys())}"
        )
    
    return await update_storage_config(operation_type, config, db)


async def update_storage_config(operation_type: str, config: Dict[str, Any], db: AsyncSession):
    """Helper function to update storage config for an operation type."""
    key = OPERATION_TYPES[operation_type]
    
    # Get existing setting
    result = await db.execute(select(SettingsModel).where(SettingsModel.key == key))
    db_setting = result.scalar_one_or_none()
    
    # Prepare the value - map frontend fields to backend format
    value = {
        "storage_type": config.get("destination_type", config.get("storage_type", "local")),
        "enabled": config.get("enabled", False),
        "format": config.get("format", "json"),
    }
    
    # Add FTP settings if destination_type is ftp
    if value["storage_type"] == "ftp":
        value.update({
            "ftp_host": config.get("ftp_host"),
            "ftp_port": config.get("ftp_port", 21),
            "ftp_user": config.get("ftp_user"),
            "ftp_password": config.get("ftp_password"),
            "ftp_path": config.get("ftp_path", "/"),
            "ftp_use_tls": config.get("ftp_use_tls", False),
        })
    elif value["storage_type"] == "local":
        value.update({
            "local_path": config.get("local_path", "./exports"),
        })
    
    if db_setting:
        db_setting.value = value
    else:
        db_setting = SettingsModel(
            key=key,
            value=value,
            description=f"Storage configuration for {operation_type}",
            is_public=False
        )
        db.add(db_setting)
    
    await db.commit()
    await db.refresh(db_setting)
    
    return format_response(operation_type, value, config.get("schedule"))


@router.get("/config")
async def get_export_config(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get export configuration (backward compatible - returns user_export)."""
    return await get_storage_config("user_export", db)


@router.get("/config/{operation_type}")
async def get_storage_config_by_type(
    operation_type: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get storage configuration for specific operation type."""
    if operation_type not in OPERATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation_type. Must be one of: {', '.join(OPERATION_TYPES.keys())}"
        )
    
    return await get_storage_config(operation_type, db)


async def get_storage_config(operation_type: str, db: AsyncSession):
    """Helper function to get storage config for an operation type."""
    key = OPERATION_TYPES[operation_type]
    result = await db.execute(select(SettingsModel).where(SettingsModel.key == key))
    db_setting = result.scalar_one_or_none()
    
    if not db_setting:
        return {
            "operation_type": operation_type,
            "enabled": False,
            "format": "json",
            "destination_type": "local",
            "local_path": "./exports",
        }
    
    value = db_setting.value
    return format_response(operation_type, value)


@router.get("/configs")
async def get_all_storage_configs(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get all storage configurations for Response Network."""
    configs = []
    
    for operation_type, key in OPERATION_TYPES.items():
        result = await db.execute(select(SettingsModel).where(SettingsModel.key == key))
        db_setting = result.scalar_one_or_none()
        
        if db_setting:
            configs.append(format_response(operation_type, db_setting.value))
        else:
            configs.append({
                "operation_type": operation_type,
                "enabled": False,
                "format": "json",
                "destination_type": "local",
                "configured": False,
            })
    
    return configs


def format_response(operation_type: str, value: dict, schedule: str = None) -> dict:
    """Format response for frontend."""
    return {
        "operation_type": operation_type,
        "enabled": value.get("enabled", False),
        "format": value.get("format", "json"),
        "destination_type": value.get("storage_type", "local"),
        "ftp_host": value.get("ftp_host"),
        "ftp_port": value.get("ftp_port"),
        "ftp_user": value.get("ftp_user"),
        "ftp_password": value.get("ftp_password"),
        "ftp_path": value.get("ftp_path"),
        "ftp_use_tls": value.get("ftp_use_tls"),
        "local_path": value.get("local_path"),
        "schedule": schedule,
        "configured": True,
    }


@router.post("/test")
async def test_export(
    current_user: User = Depends(get_current_admin_user),
):
    """Trigger a manual user export test."""
    from workers.tasks.users_exporter import export_users_to_request_network
    task = export_users_to_request_network.delay()
    return {"success": True, "message": "Export task triggered", "task_id": str(task.id)}


@router.post("/test/{operation_type}")
async def test_operation(
    operation_type: str,
    current_user: User = Depends(get_current_admin_user),
):
    """Trigger a manual test for specific operation type."""
    if operation_type not in OPERATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation_type. Must be one of: {', '.join(OPERATION_TYPES.keys())}"
        )
    
    if operation_type == "user_export":
        from workers.tasks.users_exporter import export_users_to_request_network
        task = export_users_to_request_network.delay()
    elif operation_type == "result_export":
        from workers.tasks.export_results import export_completed_results
        task = export_completed_results.delay()
    elif operation_type == "request_import":
        from workers.tasks.import_requests import import_requests_from_request_network
        task = import_requests_from_request_network.delay()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Operation {operation_type} not implemented for testing"
        )
    
    return {"success": True, "message": f"{operation_type} task triggered", "task_id": str(task.id)}


@router.post("/test-connection/{operation_type}")
async def test_ftp_connection(
    operation_type: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Test FTP connection for specific operation type."""
    if operation_type not in OPERATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation_type. Must be one of: {', '.join(OPERATION_TYPES.keys())}"
        )
    
    # Get config
    key = OPERATION_TYPES[operation_type]
    result = await db.execute(select(SettingsModel).where(SettingsModel.key == key))
    db_setting = result.scalar_one_or_none()
    
    if not db_setting:
        return {"success": False, "message": "تنظیمات پیکربندی نشده است"}
    
    config = db_setting.value
    storage_type = config.get("storage_type", "local")
    
    if storage_type == "local":
        from pathlib import Path
        path = Path(config.get("local_path", "/tmp"))
        if path.exists():
            return {"success": True, "message": f"مسیر محلی {path} موجود است"}
        else:
            return {"success": False, "message": f"مسیر محلی {path} موجود نیست"}
    
    elif storage_type == "ftp":
        import ftplib
        try:
            ftp_host = config.get("ftp_host")
            ftp_port = config.get("ftp_port") or 21
            ftp_user = config.get("ftp_user")
            ftp_password = config.get("ftp_password")
            ftp_path = config.get("ftp_path", "/")
            
            if not ftp_host or not ftp_user:
                return {"success": False, "message": "اطلاعات FTP ناقص است"}
            
            ftp = ftplib.FTP()
            ftp.connect(ftp_host, ftp_port, timeout=10)
            ftp.login(ftp_user, ftp_password)
            
            # Try to change directory
            try:
                ftp.cwd(ftp_path)
                files = ftp.nlst()
                ftp.quit()
                return {
                    "success": True, 
                    "message": f"اتصال موفق به FTP - {len(files)} فایل در مسیر {ftp_path}",
                    "files_count": len(files)
                }
            except Exception as e:
                ftp.quit()
                return {"success": False, "message": f"اتصال برقرار شد ولی مسیر {ftp_path} قابل دسترس نیست: {str(e)}"}
                
        except ftplib.error_perm as e:
            return {"success": False, "message": f"خطای احراز هویت FTP: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"خطا در اتصال FTP: {str(e)}"}
    
    return {"success": False, "message": f"نوع storage نامعتبر: {storage_type}"}


@router.get("/status")
async def get_export_status(
    current_user: User = Depends(get_current_admin_user),
):
    """Get export status."""
    return {"status": "ready", "last_export": None}
