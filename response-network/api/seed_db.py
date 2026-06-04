import asyncio
from datetime import datetime
import uuid
from typing import List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext

from db.session import async_session
from models.user import User
from models.settings import Settings, UserSettings
from models.request_type import RequestType
from models.request_type_parameter import RequestTypeParameter
from models.request_access import UserRequestAccess
from models.profile_type import ProfileType

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_profile_types(db: AsyncSession):
    profiles = [
        {"name": "admin", "description": "System Administrator", "is_active": True},
        {"name": "user", "description": "Standard User", "is_active": True}
    ]
    for p in profiles:
        result = await db.execute(select(ProfileType).where(ProfileType.name == p["name"]))
        if not result.scalar_one_or_none():
            db.add(ProfileType(**p))
    await db.commit()
    print("👥 Profile types created")

async def create_admin_user(db: AsyncSession) -> User:
    # Check if admin already exists
    result = await db.execute(select(User).where(User.email == "admin@example.com"))
    admin = result.scalar_one_or_none()
    
    if not admin:
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            hashed_password=pwd_context.hash("admin123"),
            profile_type="admin",
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        print("👤 Admin user created")
    else:
        print("👤 Admin user already exists")
    
    return admin

async def create_test_user(db: AsyncSession) -> User:
    # Create a regular test user
    result = await db.execute(select(User).where(User.email == "test@example.com"))
    test_user = result.scalar_one_or_none()
    
    if not test_user:
        test_user = User(
            username="test",
            email="test@example.com",
            full_name="Test User",
            hashed_password=pwd_context.hash("test123"),
            profile_type="user",
            is_active=True,
            is_admin=False
        )
        db.add(test_user)
        await db.commit()
        await db.refresh(test_user)
        print("👤 Test user created")
    else:
        print("👤 Test user already exists")
    
    return test_user

async def create_system_settings(db: AsyncSession):
    # Create some system-wide settings
    settings_data = [
        {"key": "max_requests_per_hour", "value": "100", "is_public": True},
        {"key": "default_timeout", "value": "30", "is_public": True},
        {"key": "maintenance_mode", "value": "false", "is_public": True},
        {"key": "api_version", "value": "1.0.0", "is_public": True},
        {"key": "admin_contact", "value": "admin@example.com", "is_public": False}
    ]
    
    for setting in settings_data:
        result = await db.execute(select(Settings).where(Settings.key == setting["key"]))
        if not result.scalar_one_or_none():
            db_setting = Settings(**setting)
            db.add(db_setting)
    
    await db.commit()
    print("⚙️ System settings created")

async def create_request_types(db: AsyncSession, admin_user: User) -> List[RequestType]:
    # Create sample request types
    request_types_data = [
        {
            "name": "Standard Request",
            "description": "Basic request type for general purposes",
            "is_active": True,
            "created_by_id": admin_user.id,
            "max_items_per_request": 1,
            "version": "1.0.0"
        },
        {
            "name": "Premium Request",
            "description": "Advanced request type with priority handling",
            "is_active": True,
            "created_by_id": admin_user.id,
            "max_items_per_request": 10,
            "version": "1.0.0"
        },
        {
            "name": "Batch Request",
            "description": "For processing multiple items at once",
            "is_active": True,
            "created_by_id": admin_user.id,
            "max_items_per_request": 100,
            "version": "1.0.0"
        }
    ]
    
    created_types = []
    for rt_data in request_types_data:
        result = await db.execute(select(RequestType).where(RequestType.name == rt_data["name"]))
        request_type = result.scalar_one_or_none()
        
        if not request_type:
            request_type = RequestType(**rt_data)
            db.add(request_type)
            await db.commit()
            await db.refresh(request_type)
            created_types.append(request_type)
        else:
            created_types.append(request_type)
    
    print("📋 Request types created")
    return created_types

async def create_request_type_parameters(db: AsyncSession, request_types: List[RequestType]):
    # Create parameters for each request type
    for rt in request_types:
        # Different parameters for each request type
        if rt.name == "Standard Request":
            params = [
                {"name": "priority", "description": "Request priority level", "parameter_type": "string", "is_required": True, "placeholder_key": "priority"},
                {"name": "category", "description": "Request category", "parameter_type": "string", "is_required": True, "placeholder_key": "category"}
            ]
        elif rt.name == "Premium Request":
            params = [
                {"name": "urgency", "description": "Urgency level", "parameter_type": "integer", "is_required": True, "placeholder_key": "urgency"},
                {"name": "callback_url", "description": "Callback URL for notifications", "parameter_type": "string", "is_required": False, "placeholder_key": "callback_url"},
                {"name": "custom_fields", "description": "Additional custom fields", "parameter_type": "json", "is_required": False, "placeholder_key": "custom_fields"}
            ]
        else:  # Batch Request
            params = [
                {"name": "batch_size", "description": "Number of items in batch", "parameter_type": "integer", "is_required": True, "placeholder_key": "batch_size"},
                {"name": "format", "description": "Data format", "parameter_type": "string", "is_required": True, "placeholder_key": "format"}
            ]
        
        for param_data in params:
            result = await db.execute(
                select(RequestTypeParameter).where(
                    RequestTypeParameter.request_type_id == rt.id,
                    RequestTypeParameter.name == param_data["name"]
                )
            )
            if not result.scalar_one_or_none():
                param = RequestTypeParameter(
                    request_type_id=rt.id,
                    **param_data
                )
                db.add(param)
    
    await db.commit()
    print("🔧 Request type parameters created")

async def create_user_settings(db: AsyncSession, user: User):
    # Create some user-specific settings
    user_settings_data = [
        {"key": "notification_enabled", "value": "true"},
        {"key": "theme", "value": "dark"},
        {"key": "language", "value": "en"}
    ]
    
    for setting in user_settings_data:
        result = await db.execute(
            select(UserSettings).where(
                UserSettings.user_id == user.id,
                UserSettings.key == setting["key"]
            )
        )
        if not result.scalar_one_or_none():
            db_setting = UserSettings(
                user_id=user.id,
                **setting
            )
            db.add(db_setting)
    
    await db.commit()
    print("⚙️ User settings created")

async def create_user_request_access(db: AsyncSession, user: User, request_types: List[RequestType]):
    # Give the test user access to all request types with different permissions
    for i, rt in enumerate(request_types):
        result = await db.execute(
            select(UserRequestAccess).where(
                UserRequestAccess.user_id == user.id,
                UserRequestAccess.request_type_id == rt.id
            )
        )
        if not result.scalar_one_or_none():
            # Set access type based on index - first gets ADMIN, others get WRITE
            access_type = "admin" if i == 0 else "write"
            access = UserRequestAccess(
                user_id=user.id,
                request_type_id=rt.id,
                max_requests_per_hour=100,
                is_active=True
            )
            db.add(access)
    
    await db.commit()
    print("🔑 User request access created")

async def main():
    print("\n🌱 Starting database seeding...")
    async with async_session() as db:
        # Create profile types first
        await create_profile_types(db)
        
        # Create users
        admin = await create_admin_user(db)
        test_user = await create_test_user(db)
        
        # Create settings
        await create_system_settings(db)
        await create_user_settings(db, test_user)
        
        # Create request types and parameters
        request_types = await create_request_types(db, admin)
        await create_request_type_parameters(db, request_types)
        
        # Create user access
        await create_user_request_access(db, test_user, request_types)
    
    print("\n✅ Database seeding completed!")
    print("\nTest Credentials:")
    print("Admin User: admin@example.com / admin123")
    print("Test User: test@example.com / test123")

if __name__ == "__main__":
    asyncio.run(main())