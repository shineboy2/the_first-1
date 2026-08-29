"""
API router for File Request Configuration management.
Admin-only endpoints for creating, listing, testing, and managing file request configs.
"""
import json
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db
from auth.dependencies import get_current_admin_user
from models.user import User
from schemas.file_request_config import (
    FileRequestConfigCreate,
    FileRequestConfigUpdate,
    FileRequestConfigRead,
    TestParseRequest,
    TestParseResponse,
    TestGenerateRequest,
    TestGenerateResponse,
)
import crud.file_request_configs as crud_frc
import crud.ftp_profiles as crud_ftp
from services.audit_service import create_audit_log

router = APIRouter(prefix="/file-request-configs", tags=["File Request Configs"])


@router.post("/", response_model=FileRequestConfigRead, status_code=status.HTTP_201_CREATED)
async def create_file_request_config(
    request: Request,
    config_in: FileRequestConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new file request configuration. Admin only."""
    # Check name uniqueness
    existing = await crud_frc.get_file_request_config_by_name(db, config_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File request config with name '{config_in.name}' already exists",
        )

    # Validate FTP profiles exist
    send_profile = await crud_ftp.get_ftp_profile(db, config_in.send_ftp_profile_id)
    if not send_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Send FTP profile not found",
        )
    receive_profile = await crud_ftp.get_ftp_profile(db, config_in.receive_ftp_profile_id)
    if not receive_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receive FTP profile not found",
        )

    created = await crud_frc.create_file_request_config(db, config_in)
    await create_audit_log(db, "FILE_REQUEST_CONFIG_CREATED", request, user_id=current_user.id, resource_type="FileRequestConfig", resource_id=str(created.id), meta={"name": created.name})
    return created


@router.get("/", response_model=List[FileRequestConfigRead])
async def list_file_request_configs(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """List all file request configurations. Admin only."""
    return await crud_frc.get_file_request_configs(
        db, skip=skip, limit=limit, active_only=active_only
    )


@router.get("/{config_id}", response_model=FileRequestConfigRead)
async def get_file_request_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get file request config details by ID. Admin only."""
    config = await crud_frc.get_file_request_config(db, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File request config not found",
        )
    return config


@router.patch("/{config_id}", response_model=FileRequestConfigRead)
async def update_file_request_config(
    request: Request,
    config_id: UUID,
    config_in: FileRequestConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update a file request configuration. Admin only."""
    # Check name uniqueness if name is being changed
    if config_in.name is not None:
        existing = await crud_frc.get_file_request_config_by_name(db, config_in.name)
        if existing and existing.id != config_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File request config with name '{config_in.name}' already exists",
            )

    # Validate FTP profiles if being changed
    if config_in.send_ftp_profile_id is not None:
        send_profile = await crud_ftp.get_ftp_profile(db, config_in.send_ftp_profile_id)
        if not send_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Send FTP profile not found",
            )
    if config_in.receive_ftp_profile_id is not None:
        receive_profile = await crud_ftp.get_ftp_profile(db, config_in.receive_ftp_profile_id)
        if not receive_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Receive FTP profile not found",
            )

    updated = await crud_frc.update_file_request_config(db, config_id, config_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File request config not found",
        )
    
    await create_audit_log(db, "FILE_REQUEST_CONFIG_UPDATED", request, user_id=current_user.id, resource_type="FileRequestConfig", resource_id=str(updated.id), meta=config_in.dict(exclude_unset=True))
    
    return updated


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_request_config(
    request: Request,
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete a file request configuration. Admin only."""
    success = await crud_frc.delete_file_request_config(db, config_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File request config not found",
        )
    
    await create_audit_log(db, "FILE_REQUEST_CONFIG_DELETED", request, user_id=current_user.id, resource_type="FileRequestConfig", resource_id=str(config_id))
    
    return None


@router.post("/test-parse", response_model=TestParseResponse)
async def test_parse_response(
    request: TestParseRequest,
    current_user: User = Depends(get_current_admin_user),
):
    """
    Test the response parser with sample JSON data.
    Allows admin to verify parser configuration before saving.
    No database access needed — pure computation.
    """
    from services.file_request_engine import FileRequestEngine

    try:
        raw_bytes = json.dumps(request.sample_json).encode("utf-8")
        parser_config = request.parser_config.model_dump()
        result = FileRequestEngine.parse_response(parser_config, raw_bytes)

        return TestParseResponse(
            success=result["success"],
            extracted_data=result.get("data"),
            error=result.get("error"),
            raw_input=request.sample_json,
        )
    except Exception as e:
        return TestParseResponse(
            success=False,
            extracted_data=None,
            error=f"Parser error: {str(e)[:300]}",
            raw_input=request.sample_json,
        )


@router.post("/{config_id}/test-generate", response_model=TestGenerateResponse)
async def test_generate_file(
    config_id: UUID,
    request: TestGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Test file generation with sample parameters.
    Generates a filename and content without actually sending to FTP.
    """
    from services.file_request_engine import FileRequestEngine

    config = await crud_frc.get_file_request_config(db, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File request config not found",
        )

    try:
        filename = FileRequestEngine.generate_filename(config, request.sample_params)
        content_bytes = FileRequestEngine.generate_file_content(config, request.sample_params)
        content_str = content_bytes.decode(config.content_encoding or "utf-8")

        return TestGenerateResponse(
            generated_filename=filename,
            generated_content=content_str,
            content_format=config.content_format,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File generation error: {str(e)[:300]}",
        )
