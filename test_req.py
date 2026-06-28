import requests

login_data = {
    "username": "admin",
    "password": "admin123"
}
try:
    response = requests.post("http://localhost:8001/api/v1/auth/login", data=login_data)
    token = response.json().get("access_token")
    if token:
        print("Logged in successfully.")
        res = requests.get("http://localhost:8001/api/v1/request-types/", headers={"Authorization": f"Bearer {token}"})
        data = res.json()
        print(f"Number of request types returned: {len(data)}")
        for rt in data:
            print(f"- {rt.get('name')}")
    else:
        print("Login failed:", response.text)
except Exception as e:
    print(e)
