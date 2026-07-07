from sqlalchemy.orm import Session
from sqlalchemy import func, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from models.user import User
from models.request import Request
from models.profile_type import ProfileType
from models.pydantic_schemas import UserCreate, UserUpdate, UserStats
from core.security import get_password_hash

async def get_users_with_stats(
    db: AsyncSession,
    profile_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20
) -> List[Dict]:
    """Get list of users with their request statistics."""
    
    # Base query for users
    query = select(User)
    if profile_type:
        query = query.where(User.profile_type == profile_type)
    if is_active is not None:  # Check for None specifically since is_active is a boolean
        query = query.where(User.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    result = []
    
    for user in users:
        stats = await get_user_stats(db, user.id)
        # Filter out SQLAlchemy internal state
        user_data = {k: v for k, v in user.__dict__.items() if not k.startswith('_')}
        user_dict = {
            **user_data,
            'stats': stats
        }
        result.append(user_dict)
    
    return result

async def get_user_with_stats(db: AsyncSession, user_id: str) -> Optional[Dict]:
    """Get detailed user information with statistics."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    stats = await get_user_stats(db, user_id)
    # Filter out SQLAlchemy internal state
    user_data = {k: v for k, v in user.__dict__.items() if not k.startswith('_')}
    return {
        **user_data,
        'stats': stats
    }

async def get_user_stats(db: AsyncSession, user_id: str) -> UserStats:
    """Calculate statistics for a specific user."""
    
    # Get base query for user's requests
    base_query = select(func.count()).select_from(Request).where(Request.user_id == user_id)
    result = await db.execute(base_query)
    total_requests = result.scalar() or 0
    
    # Calculate completed requests
    completed_query = select(func.count()).select_from(Request).where(
        Request.user_id == user_id,
        Request.status == "completed"
    )
    result = await db.execute(completed_query)
    completed_requests = result.scalar() or 0
    
    # Calculate failed requests
    failed_query = select(func.count()).select_from(Request).where(
        Request.user_id == user_id,
        Request.status == "failed"
    )
    result = await db.execute(failed_query)
    failed_requests = result.scalar() or 0
    
    # Calculate average processing time
    avg_query = select(func.avg(Request.processing_time)).select_from(Request).where(
        Request.user_id == user_id,
        Request.status.in_(["completed", "failed"])
    )
    result = await db.execute(avg_query)
    avg_time = result.scalar() or 0.0
    
    # Get today's requests
    today = datetime.utcnow().date()
    today_query = select(func.count()).select_from(Request).where(
        Request.user_id == user_id,
        func.date(Request.created_at) == today
    )
    result = await db.execute(today_query)
    requests_today = result.scalar() or 0
    
    # Get this month's requests
    month_start = today.replace(day=1)
    month_query = select(func.count()).select_from(Request).where(
        Request.user_id == user_id,
        Request.created_at >= month_start
    )
    result = await db.execute(month_query)
    requests_this_month = result.scalar() or 0
    
    return UserStats(
        total_requests=total_requests,
        completed_requests=completed_requests,
        failed_requests=failed_requests,
        avg_processing_time=float(avg_time),
        requests_today=requests_today,
        requests_this_month=requests_this_month
    )

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Create a new user."""
    # Convert UserCreate to dict, excluding password
    user_data = user_in.model_dump(exclude={'password'})
    # Add hashed password
    user_data['hashed_password'] = get_password_hash(user_in.password)
    # Create user instance
    db_user = User(**user_data)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user: User, user_in: UserUpdate) -> User:
    """Update user information."""
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Validate profile_type if being updated
    if 'profile_type' in update_data and update_data['profile_type']:
        result = await db.execute(select(ProfileType).where(ProfileType.name == update_data['profile_type']))
        profile = result.scalar_one_or_none()
        if not profile:
            raise ValueError(f"Profile type '{update_data['profile_type']}' does not exist")
    
    if update_data.get("password"):
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: Session, user_id: int) -> None:
    """Delete a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()

async def update_user_active_status(db: AsyncSession, user_id: str, is_active: bool) -> None:
    """Update user active status."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if user:
        user.is_active = is_active
        await db.commit()
    db.commit()

async def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

async def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username."""
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()

async def authenticate(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """Authenticate user by username and password."""
    from core.security import verify_password
    
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user