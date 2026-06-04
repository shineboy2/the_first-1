from fastapi.testclient import TestClient
import sys
import asyncio
sys.path.append("/app")

from main import app
from db.session import get_db_session
from models.user import User

client = TestClient(app)

def test():
    # We can override get_current_active_user to bypass auth
    from auth.dependencies import get_current_active_user
    
    async def override_get_current_active_user():
        # return a dummy user
        import uuid
        user = User()
        user.id = uuid.uuid4()
        user.username = "admin"
        return user

    app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    print("Testing /api/v1/api-keys/")
    response = client.get("/api/v1/api-keys/")
    print(response.status_code)
    print(response.text)
    
    print("Testing /api/v1/monitoring/stats")
    response = client.get("/api/v1/monitoring/stats")
    print(response.status_code)
    print(response.text)

if __name__ == "__main__":
    test()
