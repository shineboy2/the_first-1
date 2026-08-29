import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from db.session import async_session
from models.profile_type_config import ProfileTypeConfig

BUILTIN_TYPES = {
    "admin": {
        "display_name": "Administrator",
        "description": "Administrator with full access", 
        "daily_request_limit": 10000, 
        "monthly_request_limit": 300000,
        "rate_limit_per_minute": 1000,
        "rate_limit_per_hour": 10000
    },
    "user": {
        "display_name": "User",
        "description": "Standard user", 
        "daily_request_limit": 100, 
        "monthly_request_limit": 3000,
        "rate_limit_per_minute": 10,
        "rate_limit_per_hour": 100
    },
    "viewer": {
        "display_name": "Viewer",
        "description": "Read-only access", 
        "daily_request_limit": 50, 
        "monthly_request_limit": 1500,
        "rate_limit_per_minute": 5,
        "rate_limit_per_hour": 50
    },
    "basic": {
        "display_name": "Basic",
        "description": "Basic tier", 
        "daily_request_limit": 20, 
        "monthly_request_limit": 600,
        "rate_limit_per_minute": 2,
        "rate_limit_per_hour": 20
    },
    "premium": {
        "display_name": "Premium",
        "description": "Premium tier", 
        "daily_request_limit": 500, 
        "monthly_request_limit": 15000,
        "rate_limit_per_minute": 50,
        "rate_limit_per_hour": 500
    },
    "enterprise": {
        "display_name": "Enterprise",
        "description": "Enterprise tier", 
        "daily_request_limit": 5000, 
        "monthly_request_limit": 150000,
        "rate_limit_per_minute": 500,
        "rate_limit_per_hour": 5000
    }
}

async def seed_profile_types():
    print("Seeding profile types...")
    async with async_session() as db:
        for name, data in BUILTIN_TYPES.items():
            # Check if exists
            result = await db.execute(select(ProfileTypeConfig).where(ProfileTypeConfig.name == name))
            existing = result.scalar_one_or_none()
            
            if not existing:
                print(f"Creating {name}...")
                profile_type = ProfileTypeConfig(
                    name=name,
                    display_name=data["display_name"],
                    description=data["description"],
                    daily_request_limit=data["daily_request_limit"],
                    monthly_request_limit=data["monthly_request_limit"],
                    rate_limit_per_minute=data["rate_limit_per_minute"],
                    rate_limit_per_hour=data["rate_limit_per_hour"],
                    is_active=True,
                    is_builtin=True,
                    permissions={
                        "allowed_request_types": [],
                        "blocked_request_types": [],
                        "max_results_per_request": 1000
                    }
                )
                db.add(profile_type)
            else:
                print(f"{name} already exists.")
        
        await db.commit()
    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_profile_types())
