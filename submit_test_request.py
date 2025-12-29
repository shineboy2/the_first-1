import asyncio
import uuid
import os
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

# Load env variables (assuming we are in /app or similar)
# We will use defaults matching established knowledge
DB_url = "postgresql+asyncpg://requser:reqpassword123@localhost:5434/request_network_db"

async def submit_request():
    print("🚀 Connecting to Database...")
    engine = create_async_engine(DB_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Get a valid User ID (We know 'sales_agent_01' likely exists from previous sync)
        # Or just pick the first user
        result = await session.execute(text("SELECT id, username FROM users LIMIT 1"))
        user = result.first()
        
        if not user:
            print("❌ No user found! Cannot create request.")
            return

        user_id = user[0]
        print(f"👤 Using User: {user[1]} ({user_id})")

        # 2. Create a fresh request
        new_id = uuid.uuid4()
        req_type = "FlightBooking"
        params = {"origin": "THR", "destination": "DXB", "date": "2025-01-01"}
        
        print(f"🆕 Creating Request {new_id}...")
        
        await session.execute(
            text("""
                INSERT INTO requests (id, user_id, request_type, request_params, status, priority, created_at, updated_at)
                VALUES (:id, :uid, :rtype, :params, 'pending', 5, NOW(), NOW())
            """),
            {"id": new_id, "uid": user_id, "rtype": req_type, "params": str(params)} # params might need json dump if using explicit jsonb, but text params usually works if valid json string. Actually sqlalchemy params mapping handles it if native jsonb. 
            # Wait, `request_params` is usually JSONB. Passing a string might fail or work depending on driver.
            # Safer to cast or pass dict if driver supports. Asyncpg usually supports dict for jsonb.
        )
        
        # NOTE: SQLAlchemy+asyncpg usually maps dict to JSONB automatically.
        # Let's try passing the dict directly in next param style.
        # However, `text()` binding is tricky for jsonb. 
        # Making it safe: cast to jsonb in SQL.
        
        await session.execute(
            text("""
                INSERT INTO requests (id, user_id, request_type, request_params, status, priority, created_at, updated_at)
                VALUES (:id, :uid, :rtype, :params, 'pending', 5, NOW(), NOW())
            """),
            {
                "id": new_id, 
                "uid": user_id, 
                "rtype": req_type, 
                "params": '{"origin": "THR", "destination": "DXB", "date": "2025-01-01"}' # Passed as string to be safe
            } 
        )
        
        await session.commit()
        print(f"✅ Request Submitted Successfully!")
        print(f"🆔 ID: {new_id}")
        print("⏳ Status: pending")
        print("👉 The 'export_requests' worker should pick this up in ~10 seconds.")

if __name__ == "__main__":
    try:
        asyncio.run(submit_request())
    except Exception as e:
        print(f"💥 Error: {e}")
