from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, desc
from typing import List, Optional
from datetime import datetime

from models.incoming_request import IncomingRequest
from models.user import User
from models.pydantic_schemas import RequestStats

async def get_requests(
    db: AsyncSession,
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> List[IncomingRequest]:
    query = select(IncomingRequest, User.username).outerjoin(User, IncomingRequest.user_id == User.id)
    if status:
        query = query.where(IncomingRequest.status == status)
    if user_id:
        query = query.where(IncomingRequest.user_id == user_id)
    query = query.order_by(desc(IncomingRequest.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()
    
    # Manually convert to dicts to avoid Pydantic serialization issues with SQLAlchemy 2.0 objects
    results = []
    for row in rows:
        r = row[0] # IncomingRequest object
        username = row[1] # username string
        
        # Compute outcome based on status, has_error, and result
        try:
            has_error_val = getattr(r, 'has_error', False)
        except AttributeError:
            has_error_val = False
            
        if r.status in ['pending', 'processing']:
            outcome = 'pending'
        elif has_error_val or r.status == 'failed':
            outcome = 'error'
        elif r.status == 'completed' and r.result:
            outcome = 'success'
        else:
            outcome = 'unknown'
        
        # Determine if this is an external API request
        is_external_api = r.query_type == "external_api"
        api_name = None
        if is_external_api and r.query_params:
            api_name = r.query_params.get("api_type")
        
        item = {
            "id": r.id,
            "original_request_id": r.original_request_id,
            "user_id": r.user_id,
            "username": username, # Add username
            "status": r.status,
            "query_type": r.query_type,
            "query_params": r.query_params,
            "content": r.query_params, # Alias for frontend
            "error": r.error_message,   # Alias for frontend
            "created_at": r.created_at,
            "updated_at": r.updated_at or r.created_at, # Fallback
            "progress": 0.0,
            "processing_time": 0.0,
            "result": r.result.result_data if r.result else None,
            "outcome": outcome,  # Add outcome field
            "is_external_api": is_external_api,  # Add external API flag
            "api_name": api_name  # Add API name if external
        }
        results.append(item)
    return results

async def get_requests_count(
    db: AsyncSession,
    status: Optional[str] = None,
    user_id: Optional[str] = None
) -> int:
    query = select(func.count()).select_from(IncomingRequest)
    if status:
        query = query.where(IncomingRequest.status == status)
    if user_id:
        query = query.where(IncomingRequest.user_id == user_id)
    result = await db.execute(query)
    return result.scalar() or 0

async def get_request(
    db: AsyncSession, 
    request_id: str
) -> Optional[dict]:
    query = select(IncomingRequest, User.username).outerjoin(User, IncomingRequest.user_id == User.id).where(IncomingRequest.id == request_id)
    result = await db.execute(query)
    row = result.first()
    if not row:
        return None
        
    r = row[0]
    username = row[1]
    
    # Compute outcome based on status, has_error, and result
    try:
        has_error_val = getattr(r, 'has_error', False)
    except AttributeError:
        has_error_val = False
        
    if r.status in ['pending', 'processing']:
        outcome = 'pending'
    elif has_error_val or r.status == 'failed':
        outcome = 'error'
    elif r.status == 'completed' and r.result:
        outcome = 'success'
    else:
        outcome = 'unknown'
    
    # Determine if this is an external API request
    is_external_api = r.query_type == "external_api"
    api_name = None
    if is_external_api and r.query_params:
        api_name = r.query_params.get("api_type")
    
    return {
        "id": r.id,
        "original_request_id": r.original_request_id,
        "user_id": r.user_id,
        "username": username,
        "status": r.status,
        "query_type": r.query_type,
        "query_params": r.query_params,
        "content": r.query_params,
        "error": r.error_message,
        "created_at": r.created_at,
        "updated_at": r.updated_at or r.created_at,
        "progress": 0.0,
        "processing_time": 0.0,
        "result": r.result.result_data if r.result else None,
        "outcome": outcome,  # Add outcome field
        "is_external_api": is_external_api,  # Add external API flag
        "api_name": api_name  # Add API name if external
    }

async def get_request_stats(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime
) -> RequestStats:
    # Base query for total count
    total_query = select(func.count()).select_from(IncomingRequest).where(
        IncomingRequest.created_at.between(start_date, end_date)
    )
    result = await db.execute(total_query)
    total = result.scalar() or 0

    # Status-specific counts
    status_counts = {}
    for status_type in ["pending", "processing", "completed", "failed"]:
        query = select(func.count()).select_from(IncomingRequest).where(
            IncomingRequest.created_at.between(start_date, end_date),
            IncomingRequest.status == status_type
        )
        result = await db.execute(query)
        status_counts[status_type] = result.scalar() or 0

    return RequestStats(
        total=total,
        pending=status_counts["pending"],
        processing=status_counts["processing"],
        completed=status_counts["completed"],
        failed=status_counts["failed"],
        avg_processing_time=0.0 # IncomingRequest might not have this populated yet
    )