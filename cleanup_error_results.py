#!/usr/bin/env python3
"""
Script to clean up error results that contain UniqueViolation errors.
"""
import sys
sys.path.insert(0, 'response-network/api')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models.query_result import QueryResult

# Setup sync database connection
sync_engine = create_engine(
    str(settings.DATABASE_URL).replace('postgresql+asyncpg', 'postgresql'),
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def cleanup_error_results():
    db = SessionLocal()
    try:
        # Find results with UniqueViolation errors
        error_results = db.query(QueryResult).filter(
            QueryResult.result_data.contains({"error": ""})
        ).all()
        
        cleaned = 0
        for result in error_results:
            error_msg = result.result_data.get("error", "")
            if "UniqueViolation" in str(error_msg) or "duplicate key" in str(error_msg):
                # Update to a clean error message
                result.result_data = {
                    "error": "Query execution failed. Please try again.",
                    "count": 0,
                    "results": []
                }
                cleaned += 1
                print(f"Cleaned result for request {result.request_id}")
        
        if cleaned > 0:
            db.commit()
            print(f"\nCleaned {cleaned} error results.")
        else:
            print("No error results found to clean.")
        
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_error_results()
