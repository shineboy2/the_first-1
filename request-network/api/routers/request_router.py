import uuid
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request as FastAPIRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.validation import validate_request_payload
from core.rate_limiter import RateLimiter
from db.session import get_db_session

from models.user import User
from models.request import Request
from models.response import Response
from auth.dependencies import get_current_active_user

from schemas.request import RequestCreate, RequestPublic, RequestStatus, RequestDetailed
from schemas.response import ResponseDetailed

router = APIRouter(prefix="/requests", tags=["Requests"])
rate_limiter = RateLimiter()


@router.post(
    "/",
    response_model=RequestPublic,
    status_code=status.HTTP_201_CREATED)
async def submit_request(
    request_data: RequestCreate,
    http_request: FastAPIRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db_session),
):
    """
    Submit a new request for processing.

    This endpoint handles:
    1. Unique name validation
    2. Request type access verification (allowed_request_types)
    3. Rate limiting check
    4. Request creation with query parameters
    """
    try:
        # 1. Check if request name is unique
        existing_request = await db.execute(
            select(Request).where(Request.name == request_data.name)
        )
        if existing_request.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request with name '{request_data.name}' already exists"
            )

        # 2. Check if user is allowed to use this request type
        request_type = request_data.request.serviceName
        
        if not current_user.is_request_type_allowed(request_type):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to request type: {request_type}"
            )
        
        # 3. Check rate limits
        is_allowed, rate_limit_message = rate_limiter.check_rate_limit(current_user)
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=rate_limit_message
            )
        
        # 3.5 Extract query_params from fieldRequest
        field_request = request_data.request.fieldRequest
        if isinstance(field_request, dict) and "query_params" in field_request and len(field_request) == 1:
            query_params_value = field_request["query_params"]
        else:
            query_params_value = field_request
        
        # 3.6 Validate query parameters (logging only, doesn't block)
        from services.parameter_validator import ParameterValidator
        ParameterValidator.validate_and_log(
            query_params=query_params_value,
            query_type=request_type
        )

        # 3.7 Extract End-User Metadata
        sub_user_id = http_request.headers.get("X-Sub-User-Id")
        sub_user_db_id = None
        if sub_user_id:
            from models.subuser import SubUser
            stmt_sub = select(SubUser).where(
                SubUser.enterprise_user_id == current_user.id,
                SubUser.external_user_id == sub_user_id
            )
            sub_result = await db.execute(stmt_sub)
            sub_user = sub_result.scalars().first()
            if sub_user:
                sub_user_db_id = sub_user.id

        # Dump all headers into meta EXCEPT sensitive ones
        safe_headers = dict(http_request.headers)
        if "authorization" in safe_headers:
            del safe_headers["authorization"]
            
        meta_data = {
            "headers": safe_headers,
            "client_host": http_request.client.host if http_request.client else None,
        }

        # 4. Create request object
        new_request = Request(
            user_id=current_user.id,
            sub_user_id=sub_user_db_id,
            name=request_data.name,
            query_type=request_type,
            query_params=query_params_value,
            priority=current_user.priority,  # Inherit priority from user profile
            status=request_data.reqState.lower(),
            meta=meta_data,
        )
        
        db.add(new_request)
        await db.commit()
        
        # Reload request with eager loading for response to avoid MissingGreenlet error
        query = select(Request).options(selectinload(Request.response)).where(Request.id == new_request.id)
        result = await db.execute(query)
        new_request = result.scalar_one()

        return new_request
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e



@router.get("/", response_model=List[RequestPublic])
async def get_user_requests(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve a list of requests submitted by the current user.
    """
    query = (
        select(Request)
        .where(Request.user_id == current_user.id)
        .order_by(Request.created_at.desc())
        .options(selectinload(Request.response))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    requests = result.scalars().all()
    return requests


async def get_request_or_404(
    request_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
    load_response: bool = False,
) -> Request:
    """Dependency to get a request and check ownership."""
    query = select(Request).where(Request.id == request_id)
    if load_response:
        query = query.options(selectinload(Request.response))

    result = await db.execute(query)
    request = result.scalar_one_or_none()

    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    
    # A real app might allow admins to see any request, but for now, only owners can.
    if request.user_id != current_user.id and current_user.profile_type != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this request")

    return request


@router.get("/{request_id}", response_model=RequestDetailed)
async def get_request_details(
    request_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieve the full details of a specific request, including its response if available.
    """
    request = await get_request_or_404(request_id, current_user, db, load_response=True)
    return request


@router.get("/{request_id}/status", response_model=RequestStatus)
async def get_request_status(
    request_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieve just the status of a specific request (lightweight).
    """
    request = await get_request_or_404(request_id, current_user, db)
    return request


@router.get("/{request_id}/response", response_model=ResponseDetailed)
async def get_request_response(
    request_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieve the response for a completed request.
    
    Returns:
    - ResponseDetailed with full result_data, execution time, etc.
    - 404: Request not found or no response available yet
    - 403: User doesn't own the request
    """
    request = await get_request_or_404(request_id, current_user, db)
    
    # Get response from database
    response_query = select(Response).where(Response.request_id == request_id)
    response_result = await db.execute(response_query)
    response = response_result.scalar_one_or_none()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not available yet. Request is still being processed."
        )
    
    return ResponseDetailed.model_validate(response)


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def cancel_request(
    request_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db_session),
):
    """
    Cancel a request. A request can only be cancelled if its status is 'pending'.
    """
    request = await get_request_or_404(request_id, current_user, db)

    if request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel request with status '{request.status}'",
        )

    request.status = "cancelled"
    db.add(request)
    await db.commit()

    return None


@router.get("/rate-limit/status")
async def get_rate_limit_status(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get current rate limit status for the logged-in user.
    
    Returns:
    - minute: remaining requests per minute
    - hour: remaining requests per hour
    - day: remaining requests per day
    """
    remaining = rate_limiter.get_remaining(current_user)
    return {
        "user_id": str(current_user.id),
        "username": current_user.username,
        "profile_type": current_user.profile_type,
        "rate_limits": remaining
    }
