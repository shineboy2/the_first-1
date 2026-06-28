"""
Request Types Router - Serves synced request type definitions from Response Network.
Reads from IMPORT_DIR/request_types/latest.json
"""
import json
import logging
from pathlib import Path
from typing import List, Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.config import settings
from models.user import User
from auth.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/request-types", tags=["Request Types"])


# ============================================================================
# Schemas
# ============================================================================

class RequestTypeParameter(BaseModel):
    name: str
    description: Optional[str] = None
    parameter_type: str  # string, integer, text, boolean, select, date, image, video, file, json
    is_required: bool = False
    validation_rules: Optional[dict] = None
    placeholder_key: str = ""


class RequestTypeInfo(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    is_active: bool = True
    is_public: bool = False
    version: str = "1.0.0"
    max_items_per_request: int = 100
    parameters: List[RequestTypeParameter] = []


# ============================================================================
# Helpers
# ============================================================================

def _load_request_types() -> List[dict]:
    """Load request types from the synced latest.json file."""
    file_path = Path(settings.IMPORT_DIR) / "request_types" / "latest.json"
    
    if not file_path.exists():
        logger.warning(f"Request types file not found: {file_path}")
        return []
    
    try:
        from core.encryption import decrypt_data
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        
        decrypted_bytes = decrypt_data(file_bytes)
        data = json.loads(decrypted_bytes.decode("utf-8"))
        
        # Handle both list format and wrapped format
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "request_types" in data:
            return data["request_types"]
        else:
            logger.warning(f"Unexpected format in {file_path}")
            return []
    except Exception as e:
        logger.error(f"Error loading request types: {e}")
        return []


def _filter_by_user_access(request_types: List[dict], user: User) -> List[dict]:
    """Filter request types by user's allowed/blocked lists."""
    filtered = []
    for rt in request_types:
        if not rt.get("is_active", False):
            continue
        
        rt_name = rt.get("name", "")
        if user.is_request_type_allowed(rt_name):
            filtered.append(rt)
    
    return filtered


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=List[RequestTypeInfo])
async def list_request_types(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    List all available request types for the current user.
    Returns only types that the user has access to.
    """
    all_types = _load_request_types()
    user_types = _filter_by_user_access(all_types, current_user)
    return user_types


@router.get("/{type_name}", response_model=RequestTypeInfo)
async def get_request_type(
    type_name: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Get details of a specific request type by name.
    """
    all_types = _load_request_types()
    
    for rt in all_types:
        if rt.get("name") == type_name:
            if not current_user.is_request_type_allowed(type_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to request type: {type_name}"
                )
            return rt
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Request type '{type_name}' not found"
    )
