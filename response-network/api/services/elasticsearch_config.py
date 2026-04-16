"""Elasticsearch configuration service module."""
from typing import Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.elasticsearch_config import ElasticsearchConfig
from schemas.elasticsearch_config import ElasticsearchConfigCreate, ElasticsearchConfigUpdate

logger = logging.getLogger(__name__)


class ElasticsearchConfigService:
    """Service for managing Elasticsearch configuration."""
    
    def __init__(self, db: AsyncSession):
        """Initialize Elasticsearch config service."""
        self.db = db
    
    async def get_active_config(self) -> Optional[ElasticsearchConfig]:
        """Get the active Elasticsearch configuration."""
        result = await self.db.execute(
            select(ElasticsearchConfig).where(ElasticsearchConfig.is_active == True)
        )
        return result.scalars().first()
    
    async def get_all_configs(self, skip: int = 0, limit: int = 100) -> list[ElasticsearchConfig]:
        """Get all Elasticsearch configurations."""
        result = await self.db.execute(
            select(ElasticsearchConfig).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def get_config_by_id(self, config_id: str) -> Optional[ElasticsearchConfig]:
        """Get Elasticsearch configuration by ID."""
        result = await self.db.execute(
            select(ElasticsearchConfig).where(ElasticsearchConfig.id == config_id)
        )
        return result.scalars().first()
    
    async def create_config(self, data: ElasticsearchConfigCreate) -> ElasticsearchConfig:
        """Create a new Elasticsearch configuration."""
        # If this is the first config or if we want it to be active, deactivate others
        if data.is_active:
            await self.db.execute(
                select(ElasticsearchConfig).where(ElasticsearchConfig.is_active == True)
            )
            existing = (await self.db.execute(
                select(ElasticsearchConfig).where(ElasticsearchConfig.is_active == True)
            )).scalars().first()
            
            if existing:
                existing.is_active = False
                self.db.add(existing)
        
        config = ElasticsearchConfig(**data.model_dump())
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config
    
    async def update_config(self, config_id: str, data: ElasticsearchConfigUpdate) -> Optional[ElasticsearchConfig]:
        """Update Elasticsearch configuration."""
        config = await self.get_config_by_id(config_id)
        if not config:
            return None
        
        # Handle is_active flag - deactivate others if this one is being activated
        if data.is_active is not None and data.is_active and not config.is_active:
            existing = (await self.db.execute(
                select(ElasticsearchConfig).where(
                    ElasticsearchConfig.is_active == True,
                    ElasticsearchConfig.id != config_id
                )
            )).scalars().first()
            
            if existing:
                existing.is_active = False
                self.db.add(existing)
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(config, field, value)
        
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config
    
    async def delete_config(self, config_id: str) -> bool:
        """Delete Elasticsearch configuration."""
        config = await self.get_config_by_id(config_id)
        if not config:
            return False
        
        await self.db.delete(config)
        await self.db.commit()
        return True
    
    async def test_connection(self, config: ElasticsearchConfig) -> tuple[bool, str]:
        """Test connection to Elasticsearch with given configuration."""
        try:
            from elasticsearch import AsyncElasticsearch
            
            # Build connection kwargs
            kwargs = {"hosts": [config.url]}
            if config.username and config.password:
                kwargs["basic_auth"] = (config.username, config.password)
            kwargs["verify_certs"] = config.verify_ssl
            
            # Create client and test
            es_client = AsyncElasticsearch(**kwargs)
            
            try:
                info = await es_client.info()
                await es_client.close()
                return True, f"Connected successfully to {info.get('version', {}).get('number', 'Unknown')} Elasticsearch"
            except Exception as e:
                await es_client.close()
                return False, f"Connection failed: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error testing Elasticsearch connection: {str(e)}")
            return False, f"Error: {str(e)}"
