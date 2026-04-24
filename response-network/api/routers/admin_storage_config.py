"""
Admin Storage Config Router - Manage storage configuration for different operation types
Handles configuration for export/import operations (user_export, request_types_export, result_export, request_import)
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from auth.dependencies import get_current_admin_user
from db.session import get_db_session
from models.user import User as UserModel
from models.settings import Settings as SettingsModel

router = APIRouter(tags=["admin-exports"])

# Valid operation types
VALID_OPERATION_TYPES = {"user_export", "request_types_export", "result_export", "request_import"}

# Map operation types to settings keys
OPERATION_TYPE_KEYS = {
    "user_export": "storage_config_user_export",
    "request_types_export": "storage_config_request_types_export",
    "result_export": "storage_config_result_export",
    "request_import": "storage_config_request_import",
}


class StorageConfig(BaseModel):
    """Storage configuration for an operation type"""
    operation_type: str
    enabled: bool = False
    format: str = "json"
    destination_type: str = "local"  # local or ftp
    local_path: Optional[str] = None
    ftp_host: Optional[str] = None
    ftp_port: Optional[int] = None
    ftp_user: Optional[str] = None
    ftp_password: Optional[str] = None
    ftp_path: Optional[str] = None
    ftp_use_tls: Optional[bool] = False
    configured: bool = False


@router.get("/configs")
async def get_all_configs(
    current_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
) -> list:
    """Get all storage configurations for all operation types"""
    configs = []
    
    for op_type in VALID_OPERATION_TYPES:
        key = OPERATION_TYPE_KEYS[op_type]
        result = await db.execute(
            select(SettingsModel).where(SettingsModel.key == key)
        )
        db_setting = result.scalar_one_or_none()
        
        if db_setting and db_setting.value:
            config = StorageConfig(
                operation_type=op_type,
                **db_setting.value,
                configured=True
            )
        else:
            config = StorageConfig(operation_type=op_type, configured=False)
        
        configs.append(config)
    
    return configs


@router.get("/config/{operation_type}")
async def get_config(
    operation_type: str,
    current_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
) -> StorageConfig:
    """Get storage configuration for a specific operation type"""
    if operation_type not in VALID_OPERATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation_type. Must be one of: {', '.join(sorted(VALID_OPERATION_TYPES))}"
        )
    
    key = OPERATION_TYPE_KEYS[operation_type]
    result = await db.execute(
        select(SettingsModel).where(SettingsModel.key == key)
    )
    db_setting = result.scalar_one_or_none()
    
    if db_setting and db_setting.value:
        return StorageConfig(
            operation_type=operation_type,
            **db_setting.value,
            configured=True
        )
    else:
        return StorageConfig(operation_type=operation_type, configured=False)


@router.post("/config/{operation_type}")
async def update_config(
    operation_type: str,
    config_data: StorageConfig,
    current_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
) -> StorageConfig:
    """Update storage configuration for a specific operation type"""
    if operation_type not in VALID_OPERATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation_type. Must be one of: {', '.join(sorted(VALID_OPERATION_TYPES))}"
        )
    
    key = OPERATION_TYPE_KEYS[operation_type]
    
    # Prepare the value to store (exclude operation_type and configured fields)
    value = {
        "enabled": config_data.enabled,
        "format": config_data.format,
        "destination_type": config_data.destination_type,
        "local_path": config_data.local_path,
        "ftp_host": config_data.ftp_host,
        "ftp_port": config_data.ftp_port,
        "ftp_user": config_data.ftp_user,
        "ftp_password": config_data.ftp_password,
        "ftp_path": config_data.ftp_path,
        "ftp_use_tls": config_data.ftp_use_tls,
    }
    
    # Get or create the setting
    result = await db.execute(
        select(SettingsModel).where(SettingsModel.key == key)
    )
    db_setting = result.scalar_one_or_none()
    
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
    
    return StorageConfig(
        operation_type=operation_type,
        **value,
        configured=True
    )


@router.post("/test/{operation_type}")
async def test_operation(
    operation_type: str,
    current_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Test storage configuration for a specific operation type"""
    if operation_type not in VALID_OPERATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation_type. Must be one of: {', '.join(sorted(VALID_OPERATION_TYPES))}"
        )
    
    # Get the configuration
    key = OPERATION_TYPE_KEYS[operation_type]
    result = await db.execute(
        select(SettingsModel).where(SettingsModel.key == key)
    )
    db_setting = result.scalar_one_or_none()
    
    if not db_setting or not db_setting.value.get("enabled"):
        return {
            "success": False,
            "message": f"Operation {operation_type} is not enabled"
        }
    
    config = db_setting.value
    
    # Test based on destination type
    if config.get("destination_type") == "local":
        try:
            from pathlib import Path
            path = Path(config.get("local_path", "./exports"))
            path.mkdir(parents=True, exist_ok=True)
            return {
                "success": True,
                "message": f"Local path is writable: {path}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to write to local path: {str(e)}"
            }
    
    elif config.get("destination_type") == "ftp":
        try:
            from ftplib import FTP
            ftp_host = config.get("ftp_host")
            ftp_port = config.get("ftp_port") or 21  # Handle None values
            ftp_user = config.get("ftp_user")
            ftp_password = config.get("ftp_password")
            
            use_tls = config.get("ftp_use_tls", False)
            
            if use_tls:
                from ftplib import FTP_TLS
                ftp = FTP_TLS()
                ftp.connect(ftp_host, ftp_port)
                ftp.login(ftp_user, ftp_password)
                ftp.prot_p()
            else:
                ftp = FTP()
                ftp.connect(ftp_host, ftp_port)
                ftp.login(ftp_user, ftp_password)
            
            ftp.quit()
            return {
                "success": True,
                "message": f"FTP connection successful to {ftp_host}:{ftp_port}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"FTP connection failed: {str(e)}"
            }
    
    return {
        "success": False,
        "message": "Unknown destination type"
    }


@router.post("/test-connection/{operation_type}")
async def test_connection(
    operation_type: str,
    current_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Test connection for storage configuration"""
    # This is an alias for test_operation
    return await test_operation(operation_type, current_user, db)
