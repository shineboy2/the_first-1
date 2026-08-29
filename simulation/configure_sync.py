import urllib.request
import urllib.parse
import json

REQ_BASE = "http://localhost:8001/api/v1"
RESP_BASE = "http://localhost:8000/api/v1"

def login(base):
    data = urllib.parse.urlencode({"username": "admin", "password": "Admin@1234"}).encode("utf-8")
    req = urllib.request.Request(f"{base}/auth/token", data=data)
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())["access_token"]

req_token = login(REQ_BASE)
resp_token = login(RESP_BASE)

def config(base, token, path, op, host):
    url = f"{base}{path}/config/{op}"
    # Map operation to folder path
    folder = "requests" if "request_" in op and "request_types" not in op else \
             "results" if "result_" in op else \
             "request_types" if "request_types" in op else \
             "users" if "user_" in op else "data"
             
    data = json.dumps({
        "storage_type": "ftp",
        "enabled": True,
        "ftp_host": host,
        "ftp_port": 21,
        "ftp_user": "ftp_user",
        "ftp_password": "ftp_password",
        "ftp_path": f"/{folder}",
        "ftp_use_tls": False
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as res:
            print(f"Configured {op} on {base} -> /{folder}")
    except Exception as e:
        print(f"Failed to configure {op} on {base}: {e}")

# Request Network Configuration
config(REQ_BASE, req_token, "/admin/imports", "request_export", "ftp-req")
config(REQ_BASE, req_token, "/admin/imports", "result_import", "ftp-req")
config(REQ_BASE, req_token, "/admin/imports", "user_import", "ftp-req")
config(REQ_BASE, req_token, "/admin/imports", "request_types_import", "ftp-req")

# Response Network Configuration
config(RESP_BASE, resp_token, "/admin/exports", "request_import", "ftp-resp")
config(RESP_BASE, resp_token, "/admin/exports", "result_export", "ftp-resp")
config(RESP_BASE, resp_token, "/admin/exports", "user_export", "ftp-resp")
config(RESP_BASE, resp_token, "/admin/exports", "request_types_export", "ftp-resp")
