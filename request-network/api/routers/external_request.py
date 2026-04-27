import base64
import uuid
import logging
import re
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
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
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    file: Optional[UploadFile] = File(None, description="Image file to send to the external API"),
    json_data: Optional[str] = Form(None, description="JSON string with params (alternative to file upload)"),
):
    """
    Submit a new external API request.
    
    Supports two methods:
    
    1. **File Upload** (multipart/form-data):
       ```bash
       curl -X POST "http://server/api/v1/external-request/ocr_space" \\
         -H "Authorization: Bearer TOKEN" \\
         -F "file=@image.png"
       ```
    
    2. **JSON Data** (multipart/form-data with json_data field):
       ```bash
       curl -X POST "http://server/api/v1/external-request/ocr_space" \\
         -H "Authorization: Bearer TOKEN" \\
         -F 'json_data={"params": {"base64Image": "data:image/png;base64,...", "language": "eng"}, "request_name": "my_request"}'
       ```
    
    Steps:
    1. Validates user's access to `api_name`
    2. Validates rate limit
    3. Processes file OR JSON data
    4. Creates a new Request with query_type='external_api'
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
    
    # 3. Determine input method and process
    query_params = {"api_type": api_name}
    request_name = None
    
    if file and json_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send both file and JSON data. Choose one method."
        )
    
    if not file and not json_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either a file or JSON data"
        )
    
    # Method 1: File Upload
    if file:
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
            query_params["file_name"] = file.filename
            query_params["file_data"] = base64_encoded
            
        except Exception as e:
            logger.error(f"Error reading or encoding file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to read and process the uploaded file"
            )
    
    # Method 2: JSON Data
    elif json_data:
        try:
            data = json.loads(json_data)
            
            # Extract request_name if provided
            request_name = data.get("request_name")
            
            # Get params
            params = data.get("params", {})
            
            if not params:
                raise ValueError("'params' field is required in JSON data")
            
            # Process base64Image if present (remove data URI prefix)
            if "base64Image" in params:
                base64_str = params["base64Image"]
                # Remove data:image/...;base64, prefix if present
                match = re.match(r'data:image/[^;]+;base64,(.+)', base64_str)
                if match:
                    params["base64Image"] = match.group(1)
            
            # Merge params into query_params
            query_params.update(params)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON format: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error processing JSON data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing JSON data: {str(e)}"
            )

    # 4. Create internal request record
    if not request_name:
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
