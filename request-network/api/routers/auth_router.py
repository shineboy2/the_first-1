from datetime import timedelta
from typing import Annotated
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Ensure we're using local Request Network auth module
_api_dir = Path(__file__).parent.parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

# Import directly from Request Network auth
from auth.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from auth.schemas import Token
from db.session import get_db_session
from models.user import User
from routers.captcha_router import verify_captcha

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Authenticates a user and returns a JWT access token.
    """
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")
    captcha_id = form_data.get("captcha_id")
    captcha_solution = form_data.get("captcha_solution")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required",
        )

    # Verify Captcha
    if not captcha_id or not captcha_solution:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="کپچا الزامی است (Captcha is required)",
        )
        
    if not verify_captcha(captcha_id, captcha_solution):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="کپچا اشتباه است یا منقضی شده است (Invalid or expired captcha)",
        )

    # 1. Find the user by username or email
    query = select(User).where(
        (User.username == username) | (User.email == username)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # 2. Check if user exists and password is correct
    if not user or not user.verify_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Create the access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": str(user.id),
            "scopes": ["admin"] if getattr(user, "profile_type", "") == "admin" else ["user"],
        },
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}