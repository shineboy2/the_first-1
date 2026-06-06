from typing import Annotated, Callable, Sequence

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.session import get_db_session
from schemas.user import User as UserSchema
from models.user import User
from auth import security


# This tells FastAPI where to go to get a token.
# The client will send a POST request to this URL with username and password.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Decodes the JWT token, validates it, and fetches the corresponding user
    from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = security.decode_access_token(token)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception

    # Check if token is blocklisted
    if security.is_token_blocklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked or session expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from DB
    query = select(User).where(User.id == token_data.user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    # You could inject Request here to get IP, but get_current_user might be called 
    # from places without direct access to the Request object in its current signature.
    # We will rely on the auth_router for the IP check during login and the API Gateway/WAF for ongoing requests, 
    # OR we can add Request to the dependency injection.
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    A dependency that checks if the user fetched from the token is active.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# تعریف نوع برای نقش‌ها جهت خوانایی بهتر
RoleChecker = Callable[[UserSchema], bool]

def require_role(allowed_roles: Sequence[str]) -> RoleChecker:
    """
    Factory function that creates a dependency to check user roles.
    Raises an HTTPException if the user does not have any of the allowed roles.
    """
    def role_checker(current_user: Annotated[UserSchema, Depends(get_current_active_user)]) -> UserSchema:
        # بر اساس معماری، نقش کاربر در profile_type ذخیره می‌شود
        user_role = getattr(current_user, 'profile_type', 'user')
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for this user role.",
            )
        return current_user

    return role_checker

# تعریف وابستگی‌های آماده برای نقش‌های متداول
require_admin = require_role(["admin"])
require_operator = require_role(["admin", "operator"])
require_user = require_role(["admin", "operator", "user", "premium", "enterprise"])