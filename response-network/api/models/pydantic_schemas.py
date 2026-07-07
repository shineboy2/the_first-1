from pydantic import BaseModel, conint, computed_field
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int

class RequestPaginatedResponse(BaseModel):
    requests: List[Any]
    total: int
    page: int
    size: int

from schemas.user import UserBase, UserCreate, UserUpdate, UserStats, UserWithStats, UserRead as User

class RequestBase(BaseModel):
    content: Optional[Dict] = None

class RequestCreate(RequestBase):
    pass

class RequestUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    progress: Optional[float] = None

class Request(BaseModel):
    id: UUID | int | str
    original_request_id: Optional[UUID | str] = None
    user_id: UUID | int | str
    username: Optional[str] = None
    status: str
    query_type: Optional[str] = None
    query_params: Optional[Dict] = None
    content: Optional[Dict] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    error_message: Optional[str] = None
    has_error: bool = False

    processing_time: Optional[float] = None # IncomingRequest doesn't have it directly?
    progress: float = 0.0 # IncomingRequest doesn't have progress?
    created_at: datetime
    updated_at: datetime = datetime.utcnow()

    class Config:
        from_attributes = True
        orm_mode = True # For Pydantic v1
        arbitrary_types_allowed = True

    @computed_field  # type: ignore
    @property
    def effective_status(self) -> str:
        """
        Compute effective status considering has_error and error_message.
        - pending: request waiting to be processed
        - processing: request being executed
        - completed_success: response received without errors
        - completed_error: response received but contains errors
        - failed: processing failed at some stage
        """
        if self.status.lower() == "failed":
            return "failed"
        
        if self.status.lower() == "completed":
            if self.has_error or self.error_message:
                return "completed_error"
            else:
                return "completed_success"
        
        if self.status.lower() == "processing":
            return "processing"
        
        return self.status.lower()

class RequestStats(BaseModel):
    total: int
    pending: int
    processing: int
    completed: int
    completed_success: int
    completed_error: int
    failed: int
    avg_processing_time: float

class SystemHealth(BaseModel):
    status: str
    uptime: str
    last_error: Optional[str] = None
    last_check: str
    components: Dict[str, str]

class QueryStats(BaseModel):
    total_count: int
    successful_count: int
    failed_count: int
    average_processing_time: float

class SystemHealth(BaseModel):
    status: str
    components: Dict[str, str]
    components_stats: Optional[Dict[str, Dict[str, Any]]] = None
    last_check: datetime

class SystemStats(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    requests_per_minute: float
    avg_response_time: float

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    source: str
    metadata: Optional[Dict[str, str]] = None