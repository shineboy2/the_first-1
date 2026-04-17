from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.external_api import ExternalAPI
from schemas.external_api import ExternalAPICreate, ExternalAPIUpdate


async def get_external_api(db: AsyncSession, api_id: UUID) -> Optional[ExternalAPI]:
    result = await db.execute(select(ExternalAPI).where(ExternalAPI.id == api_id))
    return result.scalar_one_or_none()


async def get_external_api_by_name(db: AsyncSession, name: str) -> Optional[ExternalAPI]:
    result = await db.execute(select(ExternalAPI).where(ExternalAPI.name == name))
    return result.scalar_one_or_none()


async def get_external_apis(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[ExternalAPI]:
    result = await db.execute(select(ExternalAPI).offset(skip).limit(limit))
    return result.scalars().all()


async def create_external_api(db: AsyncSession, api: ExternalAPICreate) -> ExternalAPI:
    db_api = ExternalAPI(**api.model_dump())
    db.add(db_api)
    await db.commit()
    await db.refresh(db_api)
    return db_api


async def update_external_api(
    db: AsyncSession, api_id: UUID, api: ExternalAPIUpdate
) -> Optional[ExternalAPI]:
    db_api = await get_external_api(db, api_id)
    if db_api:
        update_data = api.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_api, key, value)
        await db.commit()
        await db.refresh(db_api)
    return db_api


async def delete_external_api(db: AsyncSession, api_id: UUID) -> bool:
    db_api = await get_external_api(db, api_id)
    if db_api:
        await db.delete(db_api)
        await db.commit()
        return True
    return False
