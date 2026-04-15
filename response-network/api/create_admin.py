import asyncio
import sys
import os
from pathlib import Path
from uuid import uuid4

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from db.session import async_session
from models import User
from models.profile_type_config import ProfileTypeConfig
from auth.security import get_password_hash
from sqlalchemy import select

async def create_admin():
    print("🌱 Creating admin user...")
    async with async_session() as session:
        # SECURITY CHECKS:
        # 1. Check if ANY admin user exists (Prevent Multiple Admins/Backdoors)
        result = await session.execute(select(User).where(User.is_admin == True))
        existing_admin = result.scalars().first()
        
        # 2. Bootstrap ProfileTypeConfigs
        builtin_profiles = [
            {
                "name": "admin",
                "display_name": "Administrator",
                "description": "System Administrator with full access",
                "permissions": {
                    "allowed_request_types": ["*"], 
                    "blocked_request_types": [],
                    "max_results_per_request": 10000
                },
                "daily_request_limit": 100000,
                "monthly_request_limit": 1000000,
                "rate_limit_per_minute": 1000,
                "rate_limit_per_hour": 10000,
                "is_active": True,
                "is_builtin": True
            },
            {
                "name": "verified_user",
                "display_name": "Verified User",
                "description": "Verified user with standard access limits",
                "permissions": {
                    "allowed_request_types": ["basic", "advanced"], 
                    "blocked_request_types": ["admin_only"],
                    "max_results_per_request": 1000
                },
                "daily_request_limit": 1000,
                "monthly_request_limit": 10000,
                "rate_limit_per_minute": 60,
                "rate_limit_per_hour": 1000,
                "is_active": True,
                "is_builtin": True
            },
            {
                "name": "basic_user",
                "display_name": "Basic User",
                "description": "Basic user with limited access",
                "permissions": {
                    "allowed_request_types": ["basic"], 
                    "blocked_request_types": ["advanced", "admin_only"],
                    "max_results_per_request": 100
                },
                "daily_request_limit": 100,
                "monthly_request_limit": 1000,
                "rate_limit_per_minute": 10,
                "rate_limit_per_hour": 100,
                "is_active": True,
                "is_builtin": True
            }
        ]

        print("  🔧 Bootstrapping profile types...")
        for p_data in builtin_profiles:
            result = await session.execute(select(ProfileTypeConfig).where(ProfileTypeConfig.name == p_data["name"]))
            existing_profile = result.scalar_one_or_none()
            
            if not existing_profile:
                print(f"    + Creating '{p_data['name']}' profile...")
                new_profile = ProfileTypeConfig(**p_data)
                session.add(new_profile)
            else:
                 print(f"    * Profile '{p_data['name']}' already exists.")
        
        await session.commit()

        # Create or Update Admin User
        admin_password = "admin123456" # User explicitly mentioned this password in prompt
        
        if existing_admin:
            print(f"  Existing admin found: {existing_admin.username}")
            
            # Force Reset Password
            print("    ! Resetting admin password to 'admin123456'...")
            existing_admin.hashed_password = get_password_hash(admin_password)
            
            # Ensure profile type is admin
            if existing_admin.profile_type != "admin":
                 print("    ! Fixing admin profile type...")
                 existing_admin.profile_type = "admin"
            
            session.add(existing_admin)
            await session.commit()
            print("  ✓ Admin password and profile updated.")
        else:
            print("  + Creating new admin user...")
            admin_user = User(
                id=uuid4(),
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash(admin_password),
                full_name="System Administrator",
                profile_type="admin",
                is_active=True,
                is_admin=True,
                daily_request_limit=10000,
                monthly_request_limit=100000,
                max_results_per_request=5000,
                allowed_indices=["*"],
            )
            session.add(admin_user)
            await session.commit()
            print(f"  ✓ Created admin user 'admin' with password: {admin_password}")

if __name__ == "__main__":
    asyncio.run(create_admin())