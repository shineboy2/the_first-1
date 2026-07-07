from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from core.dependencies import get_db
from models.pydantic_schemas import (
    Request, RequestCreate, RequestUpdate, RequestStats,
    PaginatedResponse, RequestPaginatedResponse
)
from models.user import User
from models.incoming_request import IncomingRequest
from auth.dependencies import get_current_user
from crud import requests as request_service

router = APIRouter(tags=["requests"])

@router.get("/requests", response_model=RequestPaginatedResponse)
async def list_requests(
    status: Optional[str] = Query(None, enum=['pending', 'processing', 'completed', 'failed']),
    user_id: Optional[str] = Query(None, description="Filter requests by user ID"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a paginated list of requests with optional status and user filters.
    If user_id is provided, returns requests for that specific user.
    If not provided, returns all requests (admin only).
    """
    # Check if user is trying to access other user's requests
    if user_id and user_id != str(current_user.id) and not current_user.profile_type == 'admin':
        raise HTTPException(
            status_code=403,
            detail="You can only view your own requests"
        )
    
    skip = (page - 1) * size
    # Non-admin users can only see their own requests
    if current_user.profile_type != 'admin':
        user_id = str(current_user.id)
        
    requests = await request_service.get_requests(
        db,
        status=status,
        user_id=user_id,
        skip=skip,
        limit=size
    )
    total = await request_service.get_requests_count(
        db, 
        status=status,
        user_id=user_id
    )
    
    return RequestPaginatedResponse(
        requests=requests,
        total=total,
        page=page,
        size=size
    )

@router.get("/requests/stats", response_model=RequestStats)
async def get_request_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about requests in the system.
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=7)
    if not end_date:
        end_date = datetime.utcnow()

    return await request_service.get_request_stats(db, start_date, end_date)

@router.get("/requests/{request_id}", response_model=Request)
async def get_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific request.
    """
    request = await request_service.get_request(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request
async def get_request_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about requests in the system.
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=7)
    if not end_date:
        end_date = datetime.utcnow()

    return await request_service.get_request_stats(db, start_date, end_date)


@router.post("/requests/{request_id}/retry")
async def retry_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retry a failed request.
    Resets status to 'pending' and clears error message.
    """
    result = await db.execute(select(IncomingRequest).where(IncomingRequest.id == request_id))
    request_obj = result.scalar_one_or_none()
    if not request_obj:
        raise HTTPException(status_code=404, detail="Request not found")
        
    # Check permissions
    if current_user.profile_type != 'admin' and str(request_obj.user_id) != str(current_user.id):
         raise HTTPException(status_code=403, detail="Not authorized")

    if request_obj.status != 'failed':
        raise HTTPException(status_code=400, detail="Only failed requests can be retried")

    # Reset request
    request_obj.status = 'pending'
    request_obj.error_message = None
    request_obj.retry_count = 0 
    request_obj.updated_at = datetime.utcnow()
    
    db.add(request_obj)
    await db.commit()
    await db.refresh(request_obj)
    
    return {"status": "success", "message": "Request queued for retry", "id": request_obj.id}


@router.post("/requests/retry-all")
async def retry_all_failed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retry all failed requests (Admin only).
    """
    if current_user.profile_type != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can retry all requests")
        
    # Update all failed requests
    # using explicit update for efficiency
    from models.pydantic_schemas import Request as RequestModel # Ensure we use the model class for update
    # The 'request_service' uses models.pydantic_schemas.py which seems to import the actual SQLA model?
    # Let's check imports. 'models.pydantic_schemas' typically holds Pydantic schemas. 
    # 'crud.requests' likely returns SQLA objects.
    # We need the SQLA model class for bulk update.
    # Looking at imports: 
    # from models.pydantic_schemas import ( Request, ... ) -> This looks like Pydantic.
    # Real SQLA Model is likely in `models.incoming_request` or similar based on previous steps.
    # Let's import IncomingRequest directly to be safe.
    
    from models.incoming_request import IncomingRequest
    
    result = db.query(IncomingRequest).filter(IncomingRequest.status == 'failed').update({
        IncomingRequest.status: 'pending',
        IncomingRequest.error_message: None,
        IncomingRequest.retry_count: 0,
        IncomingRequest.updated_at: datetime.utcnow()
    }, synchronize_session=False)
    
    db.commit()
    
    return {"status": "success", "message": f"Queued {result} requests for retry", "count": result}