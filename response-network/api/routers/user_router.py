from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, delete, and_

from core.dependencies import get_db
from models.schemas import UserCreate, UserUpdate, User, UserWithStats
from models.user import User as UserModel
from models.request_type import RequestType
from models.request_access import UserRequestAccess
from auth.dependencies import get_current_admin_user, get_current_user
from crud import users as user_service
from schemas.request_access import UserRequestAccessCreate, UserRequestAccessRead, UserRequestAccessReadSimple, UserRequestAccessInput
from workers.celery_app import celery_app

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=List[dict])
async def list_users(
    profile_type: Optional[str] = Query(None, enum=['admin', 'user', 'viewer']),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Get list of users with their request statistics.
    Only admins can access this endpoint.
    """
    return await user_service.get_users_with_stats(
        db,
        profile_type=profile_type,
        is_active=is_active,
        skip=skip,
        limit=limit
    )

@router.post("", response_model=User)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Create a new user.
    Only admins can create new users.
    """
    return await user_service.create_user(db, user_in)

@router.post("/force-create", response_model=User)
async def force_create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    return await user_service.create_user(db, user_in)


@router.get("/me", response_model=dict)
async def get_current_user_info(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get detailed information about the currently authenticated user including their request statistics.
    """
    return await user_service.get_user_with_stats(db, current_user.id)

@router.get("/{user_id}", response_model=UserWithStats)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Get detailed information about a specific user."""
    return await user_service.get_user_with_stats(db, user_id)


@router.post("/{user_id}/request-access", response_model=List[UserRequestAccessReadSimple])
async def grant_request_type_access(
    user_id: UUID,
    request_types: List[UserRequestAccessInput],
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Grant access to multiple request types for a user.
    Only admin users can grant access.
    """
    # Verify user exists
    user = await session.get(UserModel, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Verify request types exist
    request_type_ids = [rt.request_type_id for rt in request_types]
    result = await session.execute(
        select(RequestType).where(RequestType.id.in_(request_type_ids))
    )
    found_types = {rt.id: rt for rt in result.scalars().all()}
    
    missing_types = set(request_type_ids) - set(found_types.keys())
    if missing_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request types not found: {', '.join(str(rid) for rid in missing_types)}"
        )
    
    # Remove existing access for these request types
    await session.execute(
        delete(UserRequestAccess).where(and_(
            UserRequestAccess.user_id == user_id,
            UserRequestAccess.request_type_id.in_(request_type_ids)
        ))
    )
    
    # Create new access records
    access_records = []
    for rt_access in request_types:
        access = UserRequestAccess(
            user_id=user_id,
            request_type_id=rt_access.request_type_id,
            max_requests_per_hour=rt_access.max_requests_per_hour,
            is_active=rt_access.is_active
        )
        session.add(access)
        access_records.append(access)
    
    await session.commit()
    for record in access_records:
        await session.refresh(record)
    
    return access_records


@router.get("/{user_id}/request-access", response_model=List[UserRequestAccessReadSimple])
async def list_user_request_access(
    user_id: UUID,
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    List all request types that this user has access to.
    Only admin users can view access list.
    """
    result = await session.execute(
        select(UserRequestAccess)
        .where(UserRequestAccess.user_id == user_id)
    )
    return result.scalars().all()


@router.delete("/{user_id}/request-access/{request_type_id}")
async def revoke_request_type_access(
    user_id: UUID,
    request_type_id: UUID,
    current_user: UserModel = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Revoke access to a request type from this user.
    Only admin users can revoke access.
    """
    result = await session.execute(
        delete(UserRequestAccess).where(and_(
            UserRequestAccess.user_id == user_id,
            UserRequestAccess.request_type_id == request_type_id
        ))
    )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No access found for request type {request_type_id} for user {user_id}"
        )
    
    await session.commit()
    return {"status": "success"}


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Update user information.
    Only admins can update users.
    """
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await user_service.update_user(db, user, user_in)

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Delete a user.
    Only admins can delete users.
    """
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user_service.delete_user(db, user_id)
    return {"message": "User deleted successfully"}

@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Suspend a user's access.
    Only admins can suspend users.
    """
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user_service.update_user_status(db, user_id, "suspended")
    return {"message": "User suspended successfully"}

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Activate a suspended user.
    Only admins can activate users.
    """
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user_service.update_user_status(db, user_id, "active")
    return {"message": "User activated successfully"}


@router.post("/export/now")
async def export_users_now(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Manually trigger users export to request-network.
    
    Returns:
    - task_id: شناسه task برای بررسی وضعیت
    - status: وضعیت queue
    
    Admin only.
    """
    try:
        task = celery_app.send_task(
            "workers.tasks.users_exporter.export_users_to_request_network"
        )
        return {
            "status": "accepted",
            "task_id": task.id,
            "message": "درخواست export users در صف قرار گرفت"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در ایجاد task: {str(e)}"
        )


@router.get("/export/status/{task_id}")
async def get_users_export_status(
    task_id: str,
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    بررسی وضعیت task export.
    
    Admin only.
    """
    try:
        task = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "state": task.state,
            "result": task.result if task.successful() else None,
            "error": str(task.info) if task.failed() else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در دریافت وضعیت: {str(e)}"
        )


# ============ Password Management Endpoints ============

@router.post("/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    user_id: str,
    request_body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Reset a user's password (Admin only).
    
    **IMPORTANT RULES:**
    ✅ Only non-admin users can have password reset
    ❌ Admin users CANNOT have their password reset by another admin
    ❌ Admin passwords must be changed by themselves
    
    **Parameters:**
    - `user_id`: UUID of the user
    - `new_password`: The new password to set
    
    **Example:**
    ```json
    {
        "new_password": "TempPassword123!"
    }
    ```
    
    **Returns:**
    - message: Success message
    - username: Username of the user whose password was reset
    
    **Note:** User must change this temporary password on next login.
    """
    from core.hashing import get_password_hash
    
    if not request_body.get("new_password"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new_password is required"
        )
    
    # Get user
    user = await db.get(UserModel, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    # ❌ REJECT admin password resets (ONLY non-admins can be reset)
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="❌ CANNOT reset admin user password! Admins must change their own password using /users/change-password endpoint."
        )
    
    # Update password for non-admin users only
    user.hashed_password = get_password_hash(request_body["new_password"])
    db.add(user)
    await db.commit()
    
    # 🚀 Trigger password sync to Request Network
    try:
        from workers.tasks.password_sync import sync_password_to_request_network
        task = sync_password_to_request_network.delay(
            user_id=str(user.id),
            hashed_password=user.hashed_password
        )
        sync_task_id = task.id
        sync_status = "queued"
    except Exception as e:
        sync_task_id = None
        sync_status = f"sync_error: {str(e)}"
    
    return {
        "success": True,
        "message": f"Password reset for user {user.username}",
        "username": user.username,
        "temporary": True,
        "note": "User should change password on next login",
        "sync": {
            "status": sync_status,
            "task_id": sync_task_id,
            "message": "Password change is being synced to Request Network"
        }
    }
    
    # Update password
    user.hashed_password = get_password_hash(request_body["new_password"])
    db.add(user)
    await db.commit()
    
    return {
        "success": True,
        "message": f"Password reset for user {user.username}",
        "username": user.username,
        "temporary": True,
        "note": "User should change password on next login"
    }


@router.post("/change-password", response_model=dict)
async def change_own_password(
    request_body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Change own password (User endpoint).
    
    **Parameters:**
    - `current_password`: Current password
    - `new_password`: New password to set
    
    **Example:**
    ```json
    {
        "current_password": "oldPassword123",
        "new_password": "newPassword456"
    }
    ```
    
    **Returns:**
    - success: Whether password was changed
    - message: Success/error message
    
    **Note:** User must provide current password for verification.
    """
    from core.hashing import verify_password, get_password_hash
    
    current_password = request_body.get("current_password")
    new_password = request_body.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="current_password and new_password are required"
        )
    
    if not current_user.verify_password(current_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Prevent using same password
    if verify_password(new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    db.add(current_user)
    await db.commit()
    
    return {
        "success": True,
        "message": "Password changed successfully",
        "username": current_user.username
    }