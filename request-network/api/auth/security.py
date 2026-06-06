import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import ValidationError
import redis

from .schemas import TokenData
from core.config import settings

# Load from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_in_env")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Setup Redis client for blocklist
redis_client = redis.from_url(str(settings.REDIS_URL), decode_responses=True)

def validate_password_complexity(password: str) -> bool:
    """
    Validates password complexity:
    - Min 8 characters
    - At least 2 types of complexity (e.g. uppercase, lowercase, numbers, special characters)
    """
    if len(password) < 8:
        return False
    
    complexity_score = 0
    if re.search(r'[a-z]', password): complexity_score += 1
    if re.search(r'[A-Z]', password): complexity_score += 1
    if re.search(r'[0-9]', password): complexity_score += 1
    if re.search(r'[^a-zA-Z0-9]', password): complexity_score += 1
        
    return complexity_score >= 2

def blocklist_token(token: str, expires_in: timedelta = None):
    """
    Adds a JWT to the Redis blocklist to invalidate it.
    """
    try:
        if not expires_in:
            expires_in = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # We can extract the JTI or just block the whole token
        # For simplicity, block the whole token
        redis_client.setex(f"blocklist:{token}", int(expires_in.total_seconds()), "true")
    except Exception as e:
        # Fallback if Redis is down, we don't want to crash everything
        pass

def is_token_blocklisted(token: str) -> bool:
    """
    Checks if a JWT is blocklisted in Redis.
    """
    try:
        return redis_client.exists(f"blocklist:{token}") > 0
    except Exception:
        # Fallback if Redis is down
        return False



def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Creates a new JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenData | None:
    """
    Decodes a JWT access token and returns the payload as TokenData.
    Returns None if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Manually create TokenData to handle potential missing fields gracefully
        token_data = TokenData(
            username=payload.get("sub"),
            user_id=payload.get("user_id"),
            scopes=payload.get("scopes", [])
        )
        return token_data
    except (JWTError, ValidationError):
        # Catches errors from jose (e.g., invalid signature, expired)
        # and from Pydantic (e.g., malformed payload)
        return None