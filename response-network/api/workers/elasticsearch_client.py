from elasticsearch import AsyncElasticsearch
from datetime import datetime
import json
import logging
from typing import Optional

from core.config import settings

# Global cache for runtime ES configuration
_es_config_cache = None
_es_client_instance = None

class ElasticsearchClient:
    def __init__(self, hosts=None, username=None, password=None, verify_ssl=True):
        """
        Initialize Elasticsearch client.
        
        Args:
            hosts: List of ES hosts (overrides settings if provided)
            username: Username for basic auth
            password: Password for basic auth
            verify_ssl: Whether to verify SSL certificate
        """
        self.es = None
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        
        if hosts is None:
            # Use ELASTICSEARCH_URL from settings as fallback
            es_url = str(settings.ELASTICSEARCH_URL)
            hosts = [es_url]
        
        try:
            kwargs = {"hosts": hosts}
            if username and password:
                kwargs["basic_auth"] = (username, password)
            kwargs["verify_certs"] = verify_ssl
            
            self.es = AsyncElasticsearch(**kwargs)
        except Exception as e:
            logging.error(f"Failed to initialize Elasticsearch client: {e}")
            self.es = None
    
    @classmethod
    async def create_from_runtime_config(cls):
        """
        Create an Elasticsearch client using runtime configuration from database.
        Falls back to settings if no runtime config is found.
        """
        try:
            # Try to get runtime config from database
            from db.session import async_session
            from models.elasticsearch_config import ElasticsearchConfig
            from sqlalchemy import select
            
            async with async_session() as session:
                result = await session.execute(
                    select(ElasticsearchConfig).where(ElasticsearchConfig.is_active == True)
                )
                config = result.scalars().first()
                
                if config:
                    logging.info(f"Using runtime Elasticsearch config: {config.url}")
                    return cls(
                        hosts=[config.url],
                        username=config.username,
                        password=config.password,
                        verify_ssl=config.verify_ssl
                    )
        except Exception as e:
            logging.warning(f"Failed to load runtime Elasticsearch config, falling back to settings: {e}")
        
        # Fallback to settings
        return cls()
    
    async def close(self):
        """Close the Elasticsearch connection."""
        if self.es:
            await self.es.close()
    
    async def close_connection(self):
        """Alias for close() for compatibility."""
        await self.close()
    
    async def check_health(self):
        """Check if Elasticsearch is healthy."""
        if not self.es:
            return False
        
        try:
            response = await self.es.cluster.health()
            return response.get("status") in ["yellow", "green"]
        except Exception as e:
            logging.error(f"Elasticsearch health check failed: {e}")
            return False

    async def search(self, index, query, size=10):
        """Execute a search query on Elasticsearch."""
        try:
            response = await self.es.search(
                index=index,
                body=query,
                size=size
            )
            return response
        except Exception as e:
            logging.error(f"Elasticsearch search error: {e}")
            raise

    async def get_cluster_health(self):
        """Get cluster health information."""
        try:
            response = await self.es.cluster.health()
            return response
        except Exception as e:
            logging.error(f"Elasticsearch health check error: {e}")
            return {
                "status": "red",
                "error": str(e)
            }

    async def get_indices_stats(self):
        """Get statistics about indices."""
        try:
            response = await self.es.indices.stats()
            return response
        except Exception as e:
            logging.error(f"Elasticsearch indices stats error: {e}")
            return {
                "error": str(e)
            }