import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from core.hashing import get_password_hash


def get_database_url():
    """Construct the database URL from environment variables."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(project_root, ".env"))

    user = os.getenv("RESPONSE_DB_USER", "response_user")
    password = os.getenv("RESPONSE_DB_PASSWORD", "response_pass")
    host = os.getenv("RESPONSE_DB_HOST", "resp-db")
    port = os.getenv("RESPONSE_DB_PORT", "5432")
    db_name = os.getenv("RESPONSE_DB_NAME", "response_db")

    if not all([user, password, host, port, db_name]):
        raise ValueError("One or more database environment variables are not set.")

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"


def hash_password(password: str) -> str:
    """Hashes a password using core hashing module."""
    return get_password_hash(password)


async def seed_data():
    """
    Connects to the database and inserts initial data for development.
    """
    db_url = get_database_url()
    engine = create_async_engine(db_url, echo=True)

    async with engine.connect() as conn:
        print("--- Starting to seed data for response-network ---")
        
        # First, delete existing users
        print("Deleting existing users...")
        await conn.execute(text("DELETE FROM users"))
        await conn.commit()
        print("-> Existing users deleted.")

        # --- 1. Create Users ---
        print("Creating users...")
        users_to_create = [
            {
                "id": str(uuid.uuid4()),
                "username": "admin",
                "email": "admin@example.com",
                "hashed_password": hash_password("SuperSecureAdminP@ss!"),
                "full_name": "Admin User",
                "profile_type": "admin",
                "priority": 10,
                "is_active": True,
            },
            {
                "id": str(uuid.uuid4()),
                "username": "basic_user",
                "email": "basic@example.com",
                "hashed_password": hash_password("basic_password123"),
                "full_name": "Basic Test User",
                "profile_type": "basic",
                "priority": 5,
                "is_active": True,
            },
            {
                "id": str(uuid.uuid4()),
                "username": "premium_user",
                "email": "premium@example.com",
                "hashed_password": hash_password("premium_password456"),
                "full_name": "Premium Test User",
                "profile_type": "premium",
                "priority": 8,
                "is_active": True,
            },
        ]

        # Using text() for SQL statement to avoid ORM dependency in this script
        user_insert_stmt = text(
            """
            INSERT INTO users (id, username, email, hashed_password, full_name, profile_type, priority, is_active)
            VALUES (:id, :username, :email, :hashed_password, :full_name, :profile_type, :priority, :is_active);
            """
        )
        await conn.execute(user_insert_stmt, users_to_create)
        print(f"-> {len(users_to_create)} users created or already exist.")
        print(f"Admin password: SuperSecureAdminP@ss!")

        # Note: The original script also created sample requests.
        # This can be added back if needed, but requires fetching user IDs first.

        await conn.commit()
        print("\n--- Seeding completed successfully! ---")


if __name__ == "__main__":
    print("Starting database seeding...")
    # Install required packages if not present:
    # pip install sqlalchemy "asyncpg" "python-dotenv" "bcrypt"
    asyncio.run(seed_data())
    print("Seeding finished.")