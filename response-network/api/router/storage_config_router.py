from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from models.user import User
from models.settings import Settings
from auth.dependencies import get_current_admin_user
from core.dependencies import get_db


router = APIRouter(prefix="/settings/storage", tags=["settings"])


class StorageConfigBase(BaseModel):
    """Base schema for storage configuration"""
    storage_type: str = Field(..., description="Type of storage: 'local', 'ftp', 's3'")
    enabled: bool = Field(default=True, description="Enable/disable this configuration")
    format: str = Field(default="json", description="Export format: 'json', 'csv'")
    
    # FTP Configuration
    ftp_host: Optional[str] = Field(None, description="FTP server hostname")
    ftp_port: Optional[int] = Field(21, description="FTP server port")
    ftp_user: Optional[str] = Field(None, description="FTP username")
    ftp_password: Optional[str] = Field(None, description="FTP password")
    ftp_path: Optional[str] = Field(None, description="FTP directory path")
    ftp_use_tls: Optional[bool] = Field(False, description="Use TLS for FTP")
    
    # Local Configuration
    local_path: Optional[str] = Field(None, description="Local directory path")
    
    # S3 Configuration
    s3_bucket: Optional[str] = Field(None, description="S3 bucket name")
    s3_region: Optional[str] = Field(None, description="S3 region")
    s3_access_key: Optional[str] = Field(None, description="S3 access key")
    s3_secret_key: Optional[str] = Field(None, description="S3 secret key")
    s3_path: Optional[str] = Field(None, description="S3 path prefix")


class StorageConfigCreate(StorageConfigBase):
    """Schema for creating storage configuration"""
    operation_type: str = Field(
        ..., 
        description="Operation type: 'user_export', 'user_import', 'request_export', 'request_import', 'result_export', 'result_import'"
    )


class StorageConfigRead(StorageConfigBase):
    """Schema for reading storage configuration"""
    operation_type: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class StorageConfigUpdate(StorageConfigBase):
    """Schema for updating storage configuration"""
    pass


# Mapping of operation types to settings keys
OPERATION_TO_KEY = {
    "user_export": "export_config",  # Response Network exports users
    "user_import": "import_config",  # Request Network imports users
    "request_export": "export_config",  # Request Network exports requests
    "request_import": "request_import_config",  # Response Network imports requests
    "result_export": "result_export_config",  # Response Network exports results
    "result_import": "result_import_config",  # Request Network imports results
}


@router.post("/", response_model=StorageConfigRead, status_code=status.HTTP_201_CREATED)
async def create_or_update_storage_config(
    config: StorageConfigCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create or update storage configuration for a specific operation type.
    
    Operation Types:
    - user_export: Export users to external storage
    - user_import: Import users from external storage
    - request_export: Export requests to external storage
    - request_import: Import requests from external storage
    - result_export: Export results to external storage
    - result_import: Import results from external storage
    """
    # Validate operation type
    if config.operation_type not in OPERATION_TO_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation_type. Must be one of: {', '.join(OPERATION_TO_KEY.keys())}"
        )
    
    # Get the settings key for this operation
    settings_key = OPERATION_TO_KEY[config.operation_type]
    
    # Prepare config value
    config_value = config.model_dump(exclude={"operation_type"}, exclude_none=True)
    
    # Check if setting exists
    result = await db.execute(
        select(Settings).where(Settings.key == settings_key)
    )
    existing_setting = result.scalar_one_or_none()
    
    if existing_setting:
        # Update existing
        existing_setting.value = config_value
        await db.commit()
        await db.refresh(existing_setting)
        
        return StorageConfigRead(
            operation_type=config.operation_type,
            **config_value,
            created_at=existing_setting.created_at.isoformat() if existing_setting.created_at else None,
            updated_at=existing_setting.updated_at.isoformat() if existing_setting.updated_at else None
        )
    else:
        # Create new
        new_setting = Settings(
            key=settings_key,
            value=config_value,
            description=f"Storage configuration for {config.operation_type}"
        )
        db.add(new_setting)
        await db.commit()
        await db.refresh(new_setting)
        
        return StorageConfigRead(
            operation_type=config.operation_type,
            **config_value,
            created_at=new_setting.created_at.isoformat() if new_setting.created_at else None,
            updated_at=new_setting.updated_at.isoformat() if new_setting.updated_at else None
        )


@router.get("/{operation_type}", response_model=StorageConfigRead)
async def get_storage_config(
    operation_type: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get storage configuration for a specific operation type"""
    if operation_type not in OPERATION_TO_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation_type. Must be one of: {', '.join(OPERATION_TO_KEY.keys())}"
        )
    
    settings_key = OPERATION_TO_KEY[operation_type]
    
    result = await db.execute(
        select(Settings).where(Settings.key == settings_key)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No configuration found for {operation_type}"
        )
    
    return StorageConfigRead(
        operation_type=operation_type,
        **setting.value,
        created_at=setting.created_at.isoformat() if setting.created_at else None,
        updated_at=setting.updated_at.isoformat() if setting.updated_at else None
    )


@router.get("/", response_model=List[StorageConfigRead])
async def list_all_storage_configs(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all storage configurations"""
    configs = []
    
    for operation_type, settings_key in OPERATION_TO_KEY.items():
        result = await db.execute(
            select(Settings).where(Settings.key == settings_key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            configs.append(StorageConfigRead(
                operation_type=operation_type,
                **setting.value,
                created_at=setting.created_at.isoformat() if setting.created_at else None,
                updated_at=setting.updated_at.isoformat() if setting.updated_at else None
            ))
    
    return configs


@router.delete("/{operation_type}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_storage_config(
    operation_type: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete storage configuration for a specific operation type"""
    if operation_type not in OPERATION_TO_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation_type. Must be one of: {', '.join(OPERATION_TO_KEY.keys())}"
        )
    
    settings_key = OPERATION_TO_KEY[operation_type]
    
    result = await db.execute(
        select(Settings).where(Settings.key == settings_key)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No configuration found for {operation_type}"
        )
    
    await db.delete(setting)
    await db.commit()
    
    return None


@router.post("/{operation_type}/test", response_model=dict)
async def test_storage_config(
    operation_type: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Test storage configuration connection"""
    if operation_type not in OPERATION_TO_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation_type. Must be one of: {', '.join(OPERATION_TO_KEY.keys())}"
        )
    
    settings_key = OPERATION_TO_KEY[operation_type]
    
    result = await db.execute(
        select(Settings).where(Settings.key == settings_key)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No configuration found for {operation_type}"
        )
    
    config = setting.value
    
    # Test connection based on storage type
    if config.get("storage_type") == "ftp":
        import ftplib
        try:
            ftp = ftplib.FTP()
            ftp.connect(config["ftp_host"], config.get("ftp_port") or 21)
            ftp.login(config["ftp_user"], config["ftp_password"])
            
            # Try to change to directory
            try:
                ftp.cwd(config.get("ftp_path", "/"))
                files = ftp.nlst()
                ftp.quit()
                return {
                    "status": "success",
                    "message": f"Successfully connected to FTP and accessed {config.get('ftp_path', '/')}",
                    "files_count": len(files)
                }
            except Exception as e:
                ftp.quit()
                return {
                    "status": "warning",
                    "message": f"Connected to FTP but could not access directory: {str(e)}"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to connect to FTP: {str(e)}"
            }
    
    elif config.get("storage_type") == "local":
        from pathlib import Path
        path = Path(config.get("local_path", "/tmp"))
        if path.exists():
            return {
                "status": "success",
                "message": f"Local path {path} exists",
                "is_writable": path.is_dir() and path.stat().st_mode & 0o200
            }
        else:
            return {
                "status": "error",
                "message": f"Local path {path} does not exist"
            }
    
    return {
        "status": "error",
        "message": f"Testing not implemented for storage type: {config.get('storage_type')}"
    }
