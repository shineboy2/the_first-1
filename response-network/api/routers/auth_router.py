from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status, Response, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from auth import security
from core.config import settings
from core.hashing import verify_password
from db.session import get_db_session
from models.user import User
from routers.captcha_router import verify_captcha
from schemas.user import UserRead
from models.schemas import Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: Annotated[User, Depends(security.get_current_user)]
):
    """Get information about the currently authenticated user."""
    return current_user


from datetime import datetime, timezone
from models.audit_log import AuditLog

async def _log_audit(db: AsyncSession, user_id, action: str, client_ip: str, request: Request, request_data: dict = None):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
        request_data=request_data
    )
    db.add(audit_log)
    await db.commit()

@router.post("/login")
async def login(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Universal login endpoint that accepts both form data and JSON.
    The username can be the user's username or email address.
    """
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")
    captcha_id = form_data.get("captcha_id")
    captcha_solution = form_data.get("captcha_solution")

    # Get real client IP if behind proxy
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

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
    user = result.scalars().first()

    # 2. Check if user exists, is active, and password is correct
    if not user:
        await _log_audit(db, None, "LOGIN_FAILED", client_ip, request, {"reason": "user_not_found", "attempted_username": username})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active or not verify_password(password, user.hashed_password):
        await _log_audit(db, user.id, "LOGIN_FAILED", client_ip, request, {"reason": "invalid_password" if user.is_active else "inactive_user"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Check IP restriction (if user has allowed_ips)
    # Note: User model in response-network doesn't have allowed_ips by default maybe?
    # Let me assume it does, as I will add it if it doesn't.
    if hasattr(user, 'allowed_ips') and user.allowed_ips and client_ip not in user.allowed_ips:
        await _log_audit(db, user.id, "LOGIN_BLOCKED", client_ip, request, {"reason": "ip_not_allowed", "ip": client_ip})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Login not permitted from this IP address.",
        )
        
    await _log_audit(db, user.id, "LOGIN_SUCCESS", client_ip, request)

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