from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
import sys
from pathlib import Path
import structlog
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Ensure we're using local Request Network auth module
_api_dir = Path(__file__).parent.parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

# Import directly from Request Network auth
from auth.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, blocklist_token, redis_client
from auth.schemas import Token
from auth.dependencies import get_current_user
from db.session import get_db_session
from models.user import User
from services.audit_service import create_audit_log
from routers.captcha_router import verify_captcha
from core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
log = structlog.get_logger(__name__)

# Constants for lockout
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

class MachineLoginRequest(BaseModel):
    username: str
    password: str


@router.post(
    "/login",
    response_model=Token,
    summary="User Login (UI)",
    description="لاگین از طریق رابط کاربری. کپچا الزامی است.",
)
async def login_for_access_token(
    request: Request,
    username: str = Form(..., description="نام کاربری یا ایمیل"),
    password: str = Form(..., description="رمز عبور"),
    captcha_id: str = Form(..., description="شناسه کپچا از GET /captcha/"),
    captcha_solution: str = Form(..., description="متن خوانده‌شده از تصویر کپچا"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Authenticates a user and returns a JWT access token.
    Includes security checks: Captcha, Lockout, IP restriction, audit logging, concurrent session prevention.
    """
    # Get real client IP if behind proxy
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    # Verify Captcha
    if not verify_captcha(captcha_id, captcha_solution):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="کپچا اشتباه است یا منقضی شده است (Invalid or expired captcha)",
        )

    query = select(User).where(
        (User.username == username) | (User.email == username)
    )
    result = await db.execute(query)
    user = result.scalars().first()

    # If user doesn't exist, we don't want to leak this information, but we log it
    if not user:
        await create_audit_log(db, "LOGIN_FAILED", request, meta={"reason": "user_not_found", "attempted_username": username, "ip": client_ip})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Check if locked out
    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        await create_audit_log(db, "LOGIN_BLOCKED", request, user_id=user.id, meta={"reason": "account_locked", "ip": client_ip})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is locked. Try again later.",
        )

    # 3. Check password
    if not user.verify_password(password):
        # Increment failed attempts
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            user.failed_login_attempts = 0 # Reset counter after locking
            await create_audit_log(db, "ACCOUNT_LOCKED", request, user_id=user.id, meta={"reason": "max_failed_attempts", "ip": client_ip})
        else:
            await create_audit_log(db, "LOGIN_FAILED", request, user_id=user.id, meta={"reason": "invalid_password", "ip": client_ip})
        
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Success Login - Reset counters & update info
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_ip = client_ip
    user.last_login_date = now
    
    # Check IP restriction (Fallback to allow if not set, as per user request)
    if user.allowed_ips and client_ip not in user.allowed_ips:
        await create_audit_log(db, "LOGIN_BLOCKED", request, user_id=user.id, meta={"reason": "ip_not_allowed", "ip": client_ip})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Login not permitted from this IP address.",
        )

    await db.commit()
    await create_audit_log(db, "LOGIN_SUCCESS", request, user_id=user.id, meta={"ip": client_ip})

    # 5. Handle Concurrent Sessions (Invalidate previous active session for this user)
    # We store the latest token JTI (or just a marker) in Redis. 
    # For simplicity, we just mark the user as having a new session. 
    # A better way is storing the active token and blocklisting it.
    old_session_key = f"active_session:{user.id}"
    try:
        old_token = redis_client.get(old_session_key)
        if old_token:
            blocklist_token(old_token)
    except Exception as e:
        log.warning("Could not invalidate old session in Redis", error=str(e))

    # 6. Create the access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": str(user.id),
            "scopes": ["admin"] if getattr(user, "profile_type", "") == "admin" else ["user"],
        },
        expires_delta=access_token_expires,
    )

    # Save new active session
    try:
        redis_client.setex(old_session_key, int(access_token_expires.total_seconds()), access_token)
    except Exception:
        pass

    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/token",
    response_model=Token,
    summary="Machine/API Login (No Captcha)",
    description=(
        "لاگین مخصوص سرورها یا APIهای خارجی که امکان حل کپچا ندارند. "
        "کپچا ندارد ولی تمام چک‌های امنیتی دیگر (lockout، IP restriction، audit log) اعمال می‌شوند. "
        "توکن برگشتی JWT است و با `Authorization: Bearer <token>` در سایر endpointها استفاده می‌شود. "
        "Supports both JSON and Form Data."
    ),
)
async def machine_login(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    body: Optional[MachineLoginRequest] = None,
    username_form: Optional[str] = Form(None, alias="username"),
    password_form: Optional[str] = Form(None, alias="password"),
):
    """
    Authenticates a machine client and returns a JWT access token.
    No captcha required. All other security checks apply: lockout, IP restriction, audit logging.
    """
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    content_type = request.headers.get("content-type", "")
    
    if "application/x-www-form-urlencoded" in content_type:
        username = username_form
        password = password_form
    else:
        if not body:
            raise HTTPException(status_code=400, detail="JSON body required")
        username = body.username
        password = body.password
        
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password are required")

    query = select(User).where(
        (User.username == username) | (User.email == username)
    )
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        await create_audit_log(db, "LOGIN_FAILED", request, meta={"reason": "user_not_found", "attempted_username": username, "source": "machine", "ip": client_ip})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check lockout
    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        await create_audit_log(db, "LOGIN_BLOCKED", request, user_id=user.id, meta={"reason": "account_locked", "source": "machine", "ip": client_ip})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked. Try again later.",
        )

    # Check password
    if not user.verify_password(password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            user.failed_login_attempts = 0
            await create_audit_log(db, "ACCOUNT_LOCKED", request, user_id=user.id, meta={"reason": "max_failed_attempts", "source": "machine", "ip": client_ip})
        else:
            await create_audit_log(db, "LOGIN_FAILED", request, user_id=user.id, meta={"reason": "invalid_password", "source": "machine", "ip": client_ip})
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reset counters & update info
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_ip = client_ip
    user.last_login_date = now

    # IP restriction check
    if user.allowed_ips and client_ip not in user.allowed_ips:
        await create_audit_log(db, "LOGIN_BLOCKED", request, user_id=user.id, meta={"reason": "ip_not_allowed", "ip": client_ip, "source": "machine"})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Login not permitted from this IP address.",
        )

    await db.commit()
    await create_audit_log(db, "LOGIN_SUCCESS", request, user_id=user.id, meta={"source": "machine", "ip": client_ip})

    # Invalidate old session
    old_session_key = f"active_session:{user.id}"
    try:
        old_token = redis_client.get(old_session_key)
        if old_token:
            blocklist_token(old_token)
    except Exception as e:
        log.warning("Could not invalidate old session in Redis", error=str(e))

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": str(user.id),
            "scopes": ["admin"] if getattr(user, "profile_type", "") == "admin" else ["user"],
        },
        expires_delta=access_token_expires,
    )

    try:
        redis_client.setex(old_session_key, int(access_token_expires.total_seconds()), access_token)
    except Exception:
        pass

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Logs out the user by blocklisting the current JWT token.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        blocklist_token(token)
        
        # Remove active session marker
        try:
            redis_client.delete(f"active_session:{current_user.id}")
        except Exception:
            pass
            
    client_ip = request.client.host if request.client else "unknown"
    await create_audit_log(db, "LOGOUT", request, user_id=current_user.id, meta={"ip": client_ip})
    return {"message": "Successfully logged out"}

