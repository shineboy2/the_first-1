"""
Admin Imports Router - For Frontend Admin Panel compatibility
Provides endpoints to configure import/export settings for Request Network
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any, Annotated
import logging

from db.session import get_db_session
from auth.dependencies import require_admin
from models.user import User
from models.settings import Settings as SettingsModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/imports", tags=["admin-imports"])

# Operation types and their settings keys for Request Network
OPERATION_TYPES = {
    "user_import": "user_import_config",  # Request Network imports users from Response
    "settings_import": "settings_import_config",  # Request Network imports settings from Response
    "request_export": "request_export_config",  # Request Network exports requests to Response
    "result_import": "result_import_config",  # Request Network imports results from Response
}


@router.post("/config")
async def update_import_config(
    config: Dict[str, Any],
    current_user: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update import configuration (backward compatible - defaults to user_import).
    """
    return await update_storage_config("user_import", config, db)


@router.post("/config/{operation_type}")
async def update_storage_config_by_type(
    operation_type: str,
    config: Dict[str, Any],
    current_user: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update storage configuration for specific operation type.
    
    Operation Types:
    - user_import: Import users from Response Network
    - settings_import: Import settings from Response Network
    - request_export: Export requests to Response Network
    - result_import: Import results from Response Network
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
    
    result = await db.execute(select(SettingsModel).where(SettingsModel.key == key))
    db_setting = result.scalar_one_or_none()
    
    # Prepare the value - map frontend fields to backend format
    value = {
        "storage_type": config.get("destination_type", config.get("source_type", config.get("storage_type", "local"))),
        "enabled": config.get("enabled", False),
        "format": config.get("format", "json"),
    }
    
    # Add FTP settings if storage_type is ftp
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
            "local_path": config.get("local_path", "./imports"),
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
async def get_import_config(
    current_user: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db_session)
):
    """Get import configuration (backward compatible - returns user_import)."""
    return await get_storage_config("user_import", db)


@router.get("/config/{operation_type}")
async def get_storage_config_by_type(
    operation_type: str,
    current_user: Annotated[User, Depends(require_admin)],
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
            "local_path": "./imports",
            "configured": False,
        }
    
    value = db_setting.value
    return format_response(operation_type, value)


@router.get("/configs")
async def get_all_storage_configs(
    current_user: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db_session)
):
    """Get all storage configurations for Request Network."""
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


@router.post("/test/{operation_type}")
async def test_operation(
    operation_type: str,
    current_user: Annotated[User, Depends(require_admin)],
):
    """Trigger a manual test for specific operation type."""
    if operation_type not in OPERATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation_type. Must be one of: {', '.join(OPERATION_TYPES.keys())}"
        )
    
    try:
        if operation_type == "user_import":
            from workers.tasks.users_importer import import_users_from_response_network
            task = import_users_from_response_network.delay()
        elif operation_type == "settings_import":
            from workers.tasks.settings_importer import import_settings_from_response_network
            task = import_settings_from_response_network.delay()
        elif operation_type == "request_export":
            from workers.tasks.export_requests import export_pending_requests
            task = export_pending_requests.delay()
        elif operation_type == "result_import":
            from workers.tasks.results_importer import import_results_from_response_network
            task = import_results_from_response_network.delay()
        else:
            return {"success": False, "message": "Unknown operation type"}
        
        return {"success": True, "message": f"{operation_type} task triggered", "task_id": str(task.id)}
    except ImportError as e:
        logger.warning(f"Task for {operation_type} not implemented yet: {e}")
        return {"success": False, "message": f"Task for {operation_type} is not implemented yet"}


@router.post("/test-connection/{operation_type}")
async def test_ftp_connection(
    operation_type: str,
    current_user: Annotated[User, Depends(require_admin)],
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
            ftp_port = config.get("ftp_port", 21)
            ftp_user = config.get("ftp_user")
            ftp_password = config.get("ftp_password")
            ftp_path = config.get("ftp_path", "/")
            
            if not ftp_host or not ftp_user:
                return {"success": False, "message": "اطلاعات FTP ناقص است"}
            
            ftp = ftplib.FTP()
            ftp.connect(ftp_host, ftp_port, timeout=10)
            ftp.login(ftp_user, ftp_password)
            
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
async def get_import_status(
    current_user: Annotated[User, Depends(require_admin)],
):
    """Get import status."""
    return {"status": "ready", "last_import": None}
