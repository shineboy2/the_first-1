"""
Admin Imports Router - For Frontend Admin Panel compatibility
Provides endpoints to configure import settings from Response Network
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
import logging

from core.dependencies import get_db_session
from auth.dependencies import get_current_admin_user
from models.user import User
from models.settings import Settings as SettingsModel
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/imports", tags=["admin-imports"])


@router.post("/config")
async def update_import_config(
    config: Dict[str, Any],
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update import configuration for Request Network.
    This endpoint is called by the Admin Panel to configure FTP/Local import settings.
    
    Expected config format:
    {
        "enabled": true,
        "source_type": "ftp",
        "ftp_host": "192.168.214.139",
        "ftp_port": 21,
        "ftp_user": "request_ftp",
        "ftp_password": "ftp123",
        "ftp_path": "/users/",
        "ftp_use_tls": false
    }
    """
    try:
        key = "import_config"
        
        # Map frontend format to backend storage format
        storage_type = config.get("source_type", "local")  # Frontend uses "source_type"
        
        value = {
            "storage_type": storage_type,
            "enabled": config.get("enabled", False),
            "format": config.get("format", "json")
        }
        
        if storage_type == "ftp":
            value.update({
                "ftp_host": config.get("ftp_host"),
                "ftp_port": config.get("ftp_port", 21),
                "ftp_user": config.get("ftp_user"),
                "ftp_password": config.get("ftp_password"),
                "ftp_path": config.get("ftp_path", "/"),
                "ftp_use_tls": config.get("ftp_use_tls", False)
            })
        elif storage_type == "local":
            value.update({
                "local_path": config.get("local_path", "/app/imports")
            })
        
        # Check if setting exists
        result = await db.execute(
            select(SettingsModel).where(SettingsModel.key == key)
        )
        db_setting = result.scalar_one_or_none()
        
        if db_setting:
            # Update existing
            db_setting.value = value
            db_setting.updated_at = datetime.utcnow()
        else:
            # Create new
            db_setting = SettingsModel(
                key=key,
                value=value,
                description="Import configuration for Request Network",
                is_public=False
            )
            db.add(db_setting)
        
        await db.commit()
        await db.refresh(db_setting)
        
        # Return in frontend format
        return {
            "enabled": value.get("enabled", False),
            "format": value.get("format", "json"),
            "source_type": storage_type,
            "ftp_host": value.get("ftp_host"),
            "ftp_port": value.get("ftp_port", 21),
            "ftp_user": value.get("ftp_user"),
            "ftp_password": value.get("ftp_password"),
            "ftp_path": value.get("ftp_path"),
            "ftp_use_tls": value.get("ftp_use_tls", False),
            "local_path": value.get("local_path")
        }
        
    except Exception as e:
        logger.error(f"Failed to update import config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_import_config(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get current import configuration."""
    try:
        result = await db.execute(
            select(SettingsModel).where(SettingsModel.key == "import_config")
        )
        db_setting = result.scalar_one_or_none()
        
        if not db_setting:
            # Return default config
            return {
                "enabled": False,
                "format": "json",
                "source_type": "local",
                "local_path": "/app/imports"
            }
        
        value = db_setting.value
        storage_type = value.get("storage_type", "local")
        
        return {
            "enabled": value.get("enabled", False),
            "format": value.get("format", "json"),
            "source_type": storage_type,
            "ftp_host": value.get("ftp_host"),
            "ftp_port": value.get("ftp_port", 21),
            "ftp_user": value.get("ftp_user"),
            "ftp_password": value.get("ftp_password"),
            "ftp_path": value.get("ftp_path"),
            "ftp_use_tls": value.get("ftp_use_tls", False),
            "local_path": value.get("local_path")
        }
        
    except Exception as e:
        logger.error(f"Failed to get import config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
