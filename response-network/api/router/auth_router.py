from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status, Response, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from auth import security
from core.config import settings
from core.hashing import verify_password
from db.session import get_db_session
from models.user import User
from schemas.user import UserRead
from models.schemas import Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: Annotated[User, Depends(security.get_current_user)]
):
    """Get information about the currently authenticated user."""
    return current_user


@router.post("/login")
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db_session),
):
    """
    Universal login endpoint that accepts both form data and JSON.
    The username can be the user's username or email address.
    """
    # 1. Find the user by username or email
    query = select(User).where(
        (User.username == form_data.username) | (User.email == form_data.username)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # 2. Check if user exists, is active, and password is correct
    if (
        not user
        or not user.is_active
        or not verify_password(form_data.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token data with user_id and scopes
    token_data = {
        "user_id": str(user.id),
        "scopes": ["admin"] if user.profile_type == "admin" else ["user"]
    }
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )

    # 4. Set the token in an HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEV_MODE,
        samesite="lax",
        max_age=int(access_token_expires.total_seconds()),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.profile_type,
    }


@router.post("/logout", summary="Admin Logout")
async def logout_user(response: Response):
    """
    Logs out the current user by deleting the HttpOnly access_token cookie.
    """
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=not settings.DEV_MODE,
        samesite="lax",
    )
    return {"message": "Logout successful"}