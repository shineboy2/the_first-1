from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class APIKeyBase(BaseModel):
    name: str
    scopes: Optional[List[str]] = None
    expires_at: Optional[datetime] = None

class APIKeyCreate(APIKeyBase):
    pass

class APIKeyRead(APIKeyBase):
    id: UUID
    user_id: Optional[UUID] = None
    prefix: str
    last_used_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class APIKeyGenerated(APIKeyRead):
    api_key: str
