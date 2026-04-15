import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from db.session import get_db_session
from models.settings import Settings as SettingsModel
from models.user import User
from schemas.settings import Settings as SettingsSchema
from workers.tasks.users_importer import import_users_from_response_network
from auth.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.post("/system/trigger_import")
async def trigger_import(
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger user import task manually. Requires Admin.
    """
    if current_user.profile_type != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    import_users_from_response_network.delay()
    return {"message": "Import task triggered"}
