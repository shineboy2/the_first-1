from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from models.external_api import ExternalAPI
from schemas.external_api import ExternalAPICreate, ExternalAPIUpdate

def get_external_api(db: Session, api_id: UUID) -> Optional[ExternalAPI]:
    return db.query(ExternalAPI).filter(ExternalAPI.id == api_id).first()

def get_external_api_by_name(db: Session, name: str) -> Optional[ExternalAPI]:
    return db.query(ExternalAPI).filter(ExternalAPI.name == name).first()

def get_external_apis(
    db: Session, skip: int = 0, limit: int = 100
) -> List[ExternalAPI]:
    return db.query(ExternalAPI).offset(skip).limit(limit).all()

def create_external_api(db: Session, api: ExternalAPICreate) -> ExternalAPI:
    db_api = ExternalAPI(**api.model_dump())
    db.add(db_api)
    db.commit()
    db.refresh(db_api)
    return db_api

def update_external_api(
    db: Session, api_id: UUID, api: ExternalAPIUpdate
) -> Optional[ExternalAPI]:
    db_api = get_external_api(db, api_id)
    if db_api:
        update_data = api.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_api, key, value)
        db.commit()
        db.refresh(db_api)
    return db_api

def delete_external_api(db: Session, api_id: UUID) -> bool:
    db_api = get_external_api(db, api_id)
    if db_api:
        db.delete(db_api)
        db.commit()
        return True
    return False
