from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from pydantic import BaseModel

class TokenData(BaseModel):
    user_id: str
    scopes: list[str] = []
    exp: datetime | None = None

class SecurityConfig:
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    def __init__(self, secret_key: str):
        self.SECRET_KEY = secret_key

class SecurityService:
    def __init__(self, config: SecurityConfig):
        self.config = config

    def create_access_token(
        self,
        user_id: str,
        scopes: list[str] = [],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Creates a new JWT access token with standardized payload structure."""
        expires = datetime.now(timezone.utc) + (
            expires_delta if expires_delta
            else timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        to_encode = TokenData(
            user_id=str(user_id),
            scopes=scopes,
            exp=expires
        )
        
        return jwt.encode(
            to_encode.model_dump(),
            self.config.SECRET_KEY,
            algorithm=self.config.ALGORITHM
        )

    def decode_access_token(self, token: str) -> Optional[TokenData]:
        """Decodes and validates a JWT access token."""
        try:
            payload = jwt.decode(
                token,
                self.config.SECRET_KEY,
                algorithms=[self.config.ALGORITHM]
            )
            return TokenData(**payload)
        except (JWTError, ValueError):
            return None

    def extract_token_from_cookie(self, cookie_value: str) -> Optional[str]:
        """Extracts the token from a cookie value that uses 'bearer {token}' format."""
        if not cookie_value:
            return None
            
        token_type, _, token = cookie_value.partition(" ")
        if token_type.lower() != "bearer" or not token:
            return None
            
        return token