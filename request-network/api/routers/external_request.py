import base64
import uuid
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from core.rate_limiter import RateLimiter
from db.session import get_db_session

from models.user import User
from models.request import Request
from auth.dependencies import get_current_active_user

from schemas.request import RequestPublic

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/external-request", tags=["External Requests"])
rate_limiter = RateLimiter()

@router.post(
    "/{api_name}",
    response_model=RequestPublic,
    status_code=status.HTTP_201_CREATED)
async def submit_external_request(
    api_name: str,
    file: UploadFile = File(..., description="The image file to send to the external API"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Submit a new external API request with an image file.
    
    1. Validates user's access to `api_name`.
    2. Validates rate limit.
    3. Reads and Base64 encodes the file.
    4. Creates a new Request with query_type='external_api'.
    """
    # 1. Access Check
    if not current_user.is_external_api_allowed(api_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to external API: {api_name}"
        )
        
    # 2. Rate Limiting Check
    is_allowed, rate_limit_message = rate_limiter.check_rate_limit(current_user)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=rate_limit_message
        )
        
    # 3. Process File
    # Define a 10MB limit (can be adjusted or configured later)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    try:
        file_contents = await file.read()
        if len(file_contents) > MAX_FILE_SIZE:
             raise HTTPException(
                 status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                 detail="File size exceeds maximum allowed size (10MB)"
             )
             
        # Convert to Base64
        base64_encoded = base64.b64encode(file_contents).decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error reading or encoding file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read and process the uploaded file"
        )
        
    query_params = {
        "api_type": api_name,
        "file_name": file.filename,
        "file_data": base64_encoded
        # Note: If more parameters are needed (like strings, metadata), they can be added to the endpoint using Form()
    }

    # 4. Create internal request record
    request_name = f"ext_{api_name}_{uuid.uuid4().hex[:8]}"
    
    new_request = Request(
        user_id=current_user.id,
        name=request_name,
        query_type="external_api",
        query_params=query_params,
        priority=current_user.priority,
        status="pending",
    )
    
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)

    return new_request
