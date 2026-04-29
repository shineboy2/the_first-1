"""
Setup script for response network worker settings.
This script initializes the base worker settings in the database.
"""
import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.dependencies import get_db
from models.worker_settings import WorkerSettings
from .shared.config.base_worker_settings import BaseWorkerSettings, BASE_EXPORT_PATH

async def setup_base_worker_settings(db: AsyncSession):
    """Setup base worker settings in database."""
    base_settings = BaseWorkerSettings.get_response_base_settings()
    
    # Create base export directories
    BASE_EXPORT_PATH.mkdir(parents=True, exist_ok=True)
    for settings_dict in base_settings.values():
        Path(settings_dict["storage_path"]).mkdir(parents=True, exist_ok=True)
    
    # Create base worker settings
    for worker_name, settings_dict in base_settings.items():
        # Check if settings already exist
        existing = await db.execute(
            select(WorkerSettings)
            .where(WorkerSettings.worker_type == settings_dict["worker_type"])
        )
        if not existing.scalar_one_or_none():
            worker_settings = WorkerSettings(**settings_dict)
            db.add(worker_settings)
    
    await db.commit()

async def main():
    """Run setup."""
    async with get_db() as db:
        await setup_base_worker_settings(db)

if __name__ == "__main__":
    asyncio.run(main())