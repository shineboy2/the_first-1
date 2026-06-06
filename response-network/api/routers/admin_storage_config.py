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
from models.ftp_profile import FTPProfile

router = APIRouter(tags=["admin-exports"])

# Valid operation types
VALID_OPERATION_TYPES = {"user_export", "request_types_export", "result_export", "request_import"}

# Map operation types to settings keys (must match what workers expect)
OPERATION_TYPE_KEYS = {
    "user_export": "export_config",
    "request_types_export": "request_types_export_config",
    "result_export": "result_export_config",
    "request_import": "request_import_config",
}


class StorageConfig(BaseModel):
    """Storage configuration for an operation type"""
    operation_type: str
    enabled: bool = False
    format: str = "json"
    destination_type: str = "local"  # local or ftp
    local_path: Optional[str] = None
    ftp_profile_id: Optional[str] = None
    ftp_path: Optional[str] = None
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
            # Convert storage_type back to destination_type for frontend
            value = db_setting.value.copy()
            if 'storage_type' in value:
                value['destination_type'] = value.pop('storage_type')
            
            config = StorageConfig(
                operation_type=op_type,
                **value,
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
        # Convert storage_type back to destination_type for frontend
        value = db_setting.value.copy()
        if 'storage_type' in value:
            value['destination_type'] = value.pop('storage_type')
        
        return StorageConfig(
            operation_type=operation_type,
            **value,
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
    # Convert destination_type to storage_type for worker compatibility
    value = {
        "enabled": config_data.enabled,
        "format": config_data.format,
        "storage_type": config_data.destination_type,  # Workers expect storage_type
        "local_path": config_data.local_path,
        "ftp_profile_id": config_data.ftp_profile_id,
        "ftp_path": config_data.ftp_path,
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
    
    # Test based on destination type (check both storage_type and destination_type for compatibility)
    dest_type = config.get("storage_type") or config.get("destination_type", "local")
    
    if dest_type == "local":
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
    
    elif dest_type == "ftp":
        try:
            ftp_profile_id = config.get("ftp_profile_id")
            if not ftp_profile_id:
                return {
                    "success": False,
                    "message": "FTP Profile is not configured"
                }
            
            # Fetch FTP Profile
            profile_result = await db.execute(
                select(FTPProfile).where(FTPProfile.id == ftp_profile_id, FTPProfile.is_active == True)
            )
            ftp_profile = profile_result.scalar_one_or_none()
            
            if not ftp_profile:
                return {
                    "success": False,
                    "message": "FTP Profile not found or is inactive"
                }
            
            from ftplib import FTP
            ftp_host = ftp_profile.host
            ftp_port = ftp_profile.port or 21
            ftp_user = ftp_profile.username
            ftp_password = ftp_profile.password
            use_tls = ftp_profile.use_tls
            
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
