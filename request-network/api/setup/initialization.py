"""
Database initialization for Request Network startup
"""
import asyncio
import sys
from pathlib import Path
import logging
from passlib.context import CryptContext

# Setup paths
_api_dir = Path(__file__).resolve().parent.parent
_project_root = _api_dir.parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_api_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from db.session import AsyncSessionFactory, async_engine
from models.user import User
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a password"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.warning(f"Failed to hash password with CryptContext: {e}, using direct bcrypt")
        # Fallback to direct bcrypt
        from bcrypt import hashpw, gensalt
        # Convert to bytes and hash
        salt = gensalt(rounds=12)
        hashed = hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')


async def create_default_admin_user(session: AsyncSession):
    """Create default admin user if it doesn't exist"""
    try:
        # Check if admin user exists
        result = await session.execute(select(User).filter(User.username == "admin"))
        admin = result.scalar_one_or_none()
        
        if admin:
            logger.info("✓ Admin user already exists")
            return True
        
        # Create admin user
        admin_password = "123456"  # Default password - should be changed after first login
        hashed_pwd = get_password_hash(admin_password)
        
        admin_user = User(
            id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            username="admin",
            email="admin@airline.com",
            full_name="Administrator",
            hashed_password=hashed_pwd,
            profile_type="admin",
            is_active=True,
            allowed_request_types=[],
            blocked_request_types=[],
            allowed_external_apis=[],
            rate_limit_per_minute=1000,
            rate_limit_per_hour=10000,
            rate_limit_per_day=100000,
            daily_request_limit=100000,
            monthly_request_limit=2000000,
            priority=10,
        )
        
        session.add(admin_user)
        await session.commit()
        logger.info("✓ Default admin user created (username: admin, password: 123456)")
        logger.warning("⚠️  Please change the default admin password immediately!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        import traceback
        traceback.print_exc()
        await session.rollback()
        return False


async def initialize_database():
    """
    Initialize Request Network database:
    1. Verify database connection
    2. Create default admin user if needed
    """
    logger.info("Initializing Request Network database...")
    
    try:
        async with AsyncSessionFactory() as session:
            # Create default admin user
            await create_default_admin_user(session)
            
            logger.info("✓ Request Network database initialized successfully")
            return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Request Network: {e}")
        import traceback
        traceback.print_exc()
        return False
