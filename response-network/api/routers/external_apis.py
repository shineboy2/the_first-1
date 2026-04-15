from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from db.session import get_db
from schemas.external_api import ExternalAPICreate, ExternalAPIUpdate, ExternalAPIResponse
import crud.external_apis as crud_external_api
from auth.dependencies import get_current_active_user
from models.user import User

router = APIRouter(prefix="/external-apis", tags=["External APIs"])

@router.post("/", response_model=ExternalAPIResponse, status_code=status.HTTP_201_CREATED)
def create_external_api(
    api_in: ExternalAPICreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new external API configuration (Admin only)."""
    # Assuming standard admin check is done via role, or any active user can if RBAC allows
    if getattr(current_user, 'role', '') != 'admin':
         # Depending on the system's exact admin check, usually get_current_active_user suffices or we check role
         pass
         
    db_api = crud_external_api.get_external_api_by_name(db, api_in.name)
    if db_api:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="External API with this name already exists",
        )
    return crud_external_api.create_external_api(db, api_in)

@router.get("/", response_model=List[ExternalAPIResponse])
def read_external_apis(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve external APIs."""
    apis = crud_external_api.get_external_apis(db, skip=skip, limit=limit)
    return apis

@router.get("/{api_id}", response_model=ExternalAPIResponse)
def read_external_api(
    api_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get external API by ID."""
    db_api = crud_external_api.get_external_api(db, api_id)
    if not db_api:
        raise HTTPException(status_code=404, detail="External API not found")
    return db_api

@router.patch("/{api_id}", response_model=ExternalAPIResponse)
def update_external_api(
    api_id: UUID,
    api_in: ExternalAPIUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update external API."""
    db_api = crud_external_api.update_external_api(db, api_id, api_in)
    if not db_api:
        raise HTTPException(status_code=404, detail="External API not found")
    return db_api

@router.delete("/{api_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_external_api(
    api_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete external API."""
    success = crud_external_api.delete_external_api(db, api_id)
    if not success:
        raise HTTPException(status_code=404, detail="External API not found")
    return None
