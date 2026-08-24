"""
CRUD service for Object Storage Configuration.
Follows the same pattern as ElasticsearchConfigService.
"""
from typing import Optional, List
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.object_storage_config import ObjectStorageConfig
from schemas.object_storage_config import (
    ObjectStorageConfigCreate,
    ObjectStorageConfigUpdate,
)

logger = logging.getLogger(__name__)


class ObjectStorageConfigService:
    """Service for managing Object Storage configurations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_config(self) -> Optional[ObjectStorageConfig]:
        """Get the first active Object Storage configuration."""
        result = await self.db.execute(
            select(ObjectStorageConfig).where(ObjectStorageConfig.is_active == True)
        )
        return result.scalars().first()

    async def get_all_configs(self, skip: int = 0, limit: int = 100) -> List[ObjectStorageConfig]:
        """Get all Object Storage configurations."""
        result = await self.db.execute(
            select(ObjectStorageConfig)
            .order_by(ObjectStorageConfig.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_config_by_id(self, config_id: str) -> Optional[ObjectStorageConfig]:
        """Get Object Storage configuration by ID."""
        result = await self.db.execute(
            select(ObjectStorageConfig).where(ObjectStorageConfig.id == config_id)
        )
        return result.scalars().first()

    async def get_config_by_name(self, name: str) -> Optional[ObjectStorageConfig]:
        """Get Object Storage configuration by name."""
        result = await self.db.execute(
            select(ObjectStorageConfig).where(ObjectStorageConfig.name == name)
        )
        return result.scalars().first()

    async def create_config(self, data: ObjectStorageConfigCreate) -> ObjectStorageConfig:
        """Create a new Object Storage configuration."""
        # Build model instance (exclude secret_key from dump)
        config_data = data.model_dump(exclude={"secret_key"})
        config = ObjectStorageConfig(**config_data)

        # Encrypt and set secret key
        config.set_secret_key(data.secret_key)

        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def update_config(
        self, config_id: str, data: ObjectStorageConfigUpdate
    ) -> Optional[ObjectStorageConfig]:
        """Update an existing Object Storage configuration."""
        config = await self.get_config_by_id(config_id)
        if not config:
            return None

        update_data = data.model_dump(exclude_unset=True, exclude={"secret_key"})
        for field, value in update_data.items():
            if value is not None:
                setattr(config, field, value)

        # Handle secret_key update separately (encrypt)
        if data.secret_key is not None:
            config.set_secret_key(data.secret_key)

        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def delete_config(self, config_id: str) -> bool:
        """Delete an Object Storage configuration."""
        config = await self.get_config_by_id(config_id)
        if not config:
            return False

        await self.db.delete(config)
        await self.db.commit()
        return True

    async def test_connection(self, config: ObjectStorageConfig) -> tuple:
        """
        Test connection to Object Storage.
        Runs synchronously (boto3 is sync) but safe for occasional admin calls.

        Returns:
            (success: bool, message: str)
        """
        try:
            from services.object_storage_handler import ObjectStorageHandler
            handler = ObjectStorageHandler(config)
            success, message = handler.test_connection()

            # Update test tracking fields
            config.last_tested_at = datetime.utcnow()
            config.last_test_result = f"{'OK' if success else 'FAILED'}: {message[:450]}"
            self.db.add(config)
            await self.db.commit()

            return (success, message)
        except Exception as e:
            logger.error(f"Error testing Object Storage connection: {str(e)}")
            return (False, f"Error: {str(e)}")
