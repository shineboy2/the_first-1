from typing import List, Dict, Any
from pydantic import BaseModel

class SystemStats(BaseModel):
    """
    Schema for representing overall system statistics.
    """
    total_users: int
    active_users: int
    total_requests: int
    pending_requests: int
    completed_requests: int
    failed_requests: int
    total_export_batches: int
    total_import_batches: int
    
    # New detailed stats for Dashboard
    requests_by_type: List[Dict[str, Any]] = []
    user_request_stats: List[Dict[str, Any]] = []
    request_types_stats: Dict[str, int] = {"active": 0, "inactive": 0}

    class Config:
        from_attributes = True