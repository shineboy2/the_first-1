import requests

def test():
    # Login
    url = "http://localhost:8001/api/v1/auth/login"
    data = {"username": "admin@airline.com", "password": "123"}
    # Wait, the user said they couldn't login. Ah! Wait!
    # They said: "سمت شبکه درخواست نمیتونم لاگین کنم:"
    # And then I added Captcha! So login requires captcha.
    # Let me bypass login and just hit the endpoints from inside the app if possible, but FastAPI requires auth.
    pass
