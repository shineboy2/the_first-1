import os
from fastapi.testclient import TestClient
from api.main import app
from api.db.session import SessionLocal
from api.models.user import User

client = TestClient(app)

db = SessionLocal()
user = db.query(User).filter(User.username == "admin").first()

if user:
    from api.auth.utils import create_access_token
    token = create_access_token(data={"sub": user.username})
    response = client.get("/api/v1/request-types/", headers={"Authorization": f"Bearer {token}"})
    print(response.status_code)
    print(response.json())
else:
    print("No admin user found")
