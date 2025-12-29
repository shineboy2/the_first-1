"""
Export settings to Request Network
"""
from datetime import datetime
import json
import asyncio

from celery import shared_task
from sqlalchemy import select

from db.session import async_session
from models.settings import Settings
from services.export_storage import ExportStorageService


@shared_task
def export_settings_to_request_network():
    """Export all public settings to Request Network."""
    
    async def _export():
        async with async_session() as db:
            # Get all public settings
            result = await db.execute(
                select(Settings).where(Settings.is_public == True)
            )
            settings_list = result.scalars().all()

            # Retrieve dynamic export configuration
            config_result = await db.execute(
                select(Settings).where(Settings.key == "export_config")
            )
            config_setting = config_result.scalar_one_or_none()
            config = config_setting.value if config_setting else None
            
            # Prepare export data
            export_data = {
                "settings": [
                    {
                        "id": str(setting.id),
                        "key": setting.key,
                        "value": setting.value,
                        "description": setting.description,
                        "is_public": setting.is_public,
                        "created_at": setting.created_at.isoformat() if setting.created_at else None,
                    }
                    for setting in settings_list
                ],
                "exported_at": datetime.utcnow().isoformat(),
                "total_count": len(settings_list),
            }
            
            # Save using ExportStorageService
            filename = f"settings_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            json_data = json.dumps(export_data, indent=2, default=str).encode('utf-8')
            file_path = await ExportStorageService.save_export_file(filename, json_data, config)
            
            return {
                "status": "success",
                "exported_at": export_data["exported_at"],
                "total_count": len(settings_list),
                "file": file_path
            }
    
    return asyncio.run(_export())