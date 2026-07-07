from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.config import settings
from core.security import create_access_token
from core.dependencies import get_db
from crud import users as user_service
from models.pydantic_schemas import Token, UserCreate, User
from models.user import User as UserModel
from auth.dependencies import get_current_active_user

router = APIRouter(tags=["authentication"])

from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    db: Session = Depends(get_db),
    login_data: LoginRequest = Body(...)
) -> Any:
    """Simple login endpoint that accepts JSON"""
    user = await user_service.authenticate(
        db, username=login_data.username, password=login_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/login/test-token", response_model=User)
async def test_token(current_user: UserModel = Depends(get_current_active_user)) -> Any:
    """Test access token."""
    return current_user