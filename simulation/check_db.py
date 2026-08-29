import sys
import json
sys.path.append("/home/docker/my-distributed-app/the_first-1/response-network/api")
from core.database import SessionLocal
from models.query_result import QueryResult
from models.incoming_request import IncomingRequest
from sqlalchemy.orm import class_mapper

db = SessionLocal()
req = db.query(IncomingRequest).order_by(IncomingRequest.created_at.desc()).first()
if req:
    print(f"Latest Request ID: {req.id}")
    print(f"Query Type: {req.query_type}")
    print(f"Status: {req.status}")
    res = db.query(QueryResult).filter(QueryResult.request_id == req.id).first()
    if res:
        print(f"Result Count: {res.result_count}")
        print("Result Data (first 1000 chars):")
        print(json.dumps(res.result_data, indent=2)[:1000])
    else:
        print("No result found.")
else:
    print("No requests found.")
