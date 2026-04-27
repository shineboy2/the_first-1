#!/usr/bin/env python3
"""
Script to reset stuck requests that are in 'processing' state for too long.
"""
import sys
sys.path.insert(0, 'response-network/api')

from datetime import datetime, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models.incoming_request import IncomingRequest

# Setup sync database connection
sync_engine = create_engine(
    str(settings.DATABASE_URL).replace('postgresql+asyncpg', 'postgresql'),
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def reset_stuck_requests():
    db = SessionLocal()
    try:
        # Find requests stuck in 'processing' for more than 5 minutes
        stuck_threshold = datetime.utcnow() - timedelta(minutes=5)
        
        stuck_requests = db.query(IncomingRequest).filter(
            IncomingRequest.status == "processing",
            IncomingRequest.started_at < stuck_threshold
        ).all()
        
        if not stuck_requests:
            print("No stuck requests found.")
            return
        
        print(f"Found {len(stuck_requests)} stuck requests:")
        for req in stuck_requests:
            print(f"  - {req.id}: started at {req.started_at}, retry_count={req.retry_count}")
            
            # Reset to pending if retry_count < 3
            if req.retry_count < 3:
                req.status = "pending"
                req.started_at = None
                req.assigned_worker = None
                print(f"    -> Reset to pending (retry {req.retry_count}/3)")
            else:
                req.status = "failed"
                req.completed_at = datetime.utcnow()
                print(f"    -> Marked as failed (max retries exceeded)")
        
        db.commit()
        print(f"\nSuccessfully reset {len(stuck_requests)} requests.")
        
    finally:
        db.close()

if __name__ == "__main__":
    reset_stuck_requests()
