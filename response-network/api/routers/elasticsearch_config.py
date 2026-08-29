"""Elasticsearch configuration router module."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.dependencies import get_db
from auth.dependencies import get_current_admin_user
from models.user import User
from models.elasticsearch_config import ElasticsearchConfig
from schemas.elasticsearch_config import (
    ElasticsearchConfigCreate,
    ElasticsearchConfigRead,
    ElasticsearchConfigReadWithPassword,
    ElasticsearchConfigUpdate
)
from services.elasticsearch_config import ElasticsearchConfigService
from services.audit_service import create_audit_log

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/elasticsearch",
    tags=["admin-elasticsearch"],
)


@router.get("/config/active", response_model=ElasticsearchConfigRead)
async def get_active_elasticsearch_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get the currently active Elasticsearch configuration."""
    service = ElasticsearchConfigService(db)
    config = await service.get_active_config()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Elasticsearch configuration found"
        )
    
    return config.to_read()


@router.get("/config", response_model=list[ElasticsearchConfigRead])
async def list_elasticsearch_configs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """List all Elasticsearch configurations."""
    service = ElasticsearchConfigService(db)
    configs = await service.get_all_configs(skip=skip, limit=limit)
    return [config.to_read() for config in configs]


@router.get("/config/{config_id}", response_model=ElasticsearchConfigRead)
async def get_elasticsearch_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get a specific Elasticsearch configuration by ID."""
    service = ElasticsearchConfigService(db)
    config = await service.get_config_by_id(config_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Elasticsearch configuration not found"
        )
    
    return config.to_read()


@router.post("/config", response_model=ElasticsearchConfigRead, status_code=status.HTTP_201_CREATED)
async def create_elasticsearch_config(
    request: Request,
    data: ElasticsearchConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new Elasticsearch configuration."""
    service = ElasticsearchConfigService(db)
    
    # Test connection first
    temp_config = ElasticsearchConfig(**data.model_dump())
    success, message = await service.test_connection(temp_config)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Elasticsearch connection test failed: {message}"
        )
    
    config = await service.create_config(data)
    logger.info(f"Created Elasticsearch configuration: {config.id}")
    
    await create_audit_log(db, "ES_CONFIG_CREATED", request, user_id=current_user.id, resource_type="ElasticsearchConfig", resource_id=str(config.id), meta={"url": config.url})
    
    return config.to_read()


@router.put("/config/{config_id}", response_model=ElasticsearchConfigRead)
async def update_elasticsearch_config(
    request: Request,
    config_id: str,
    data: ElasticsearchConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update an Elasticsearch configuration."""
    service = ElasticsearchConfigService(db)
    
    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Elasticsearch configuration not found"
        )
    
    # Test connection if URL or credentials are being updated
    if data.url or data.username or data.password:
        test_config_data = {
            "url": data.url or config.url,
            "username": data.username or config.username,
            "password": data.password or config.password,
            "verify_ssl": data.verify_ssl if data.verify_ssl is not None else config.verify_ssl,
            "is_active": data.is_active if data.is_active is not None else config.is_active,
        }
        test_config = ElasticsearchConfig(**test_config_data)
        success, message = await service.test_connection(test_config)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Elasticsearch connection test failed: {message}"
            )
    
    updated_config = await service.update_config(config_id, data)
    logger.info(f"Updated Elasticsearch configuration: {config_id}")
    
    await create_audit_log(db, "ES_CONFIG_UPDATED", request, user_id=current_user.id, resource_type="ElasticsearchConfig", resource_id=config_id, meta=data.dict(exclude_unset=True))
    
    return updated_config.to_read()


@router.delete("/config/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_elasticsearch_config(
    request: Request,
    config_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete an Elasticsearch configuration."""
    service = ElasticsearchConfigService(db)
    
    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Elasticsearch configuration not found"
        )
    
    if config.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the active Elasticsearch configuration"
        )
    
    await service.delete_config(config_id)
    logger.info(f"Deleted Elasticsearch configuration: {config_id}")
    
    await create_audit_log(db, "ES_CONFIG_DELETED", request, user_id=current_user.id, resource_type="ElasticsearchConfig", resource_id=config_id, meta={"url": config.url})


@router.post("/config/{config_id}/test", response_model=dict)
async def test_elasticsearch_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Test connection to Elasticsearch with a specific configuration."""
    service = ElasticsearchConfigService(db)
    
    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Elasticsearch configuration not found"
        )
    
    success, message = await service.test_connection(config)
    
    return {
        "success": success,
        "message": message,
        "config_id": config_id
    }


@router.post("/config/test-new", response_model=dict)
async def test_new_elasticsearch_config(
    data: ElasticsearchConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Test connection with a new (not yet created) Elasticsearch configuration."""
    service = ElasticsearchConfigService(db)
    
    temp_config = ElasticsearchConfig(**data.model_dump())
    success, message = await service.test_connection(temp_config)
    
    return {
        "success": success,
        "message": message
    }
