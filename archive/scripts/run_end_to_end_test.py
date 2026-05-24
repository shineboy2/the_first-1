"""
End-to-end test script (Response -> Request)

Steps:
1. Login to Response Network as admin (admin@example.com / admin123)
2. Create a non-admin user (testuser_e2e)
3. Trigger users export on Response Network
4. Run Request Network importer script (reads from response exports path)
5. Login to Request Network with created user's credentials

This script assumes both APIs are reachable at:
- Response: http://127.0.0.1:8001
- Request: http://127.0.0.1:8000

It also assumes the repo layout where request-network can access response-network exports via the file system.
"""
import time
import json
import http.client
import urllib.parse
import subprocess
import os
from pathlib import Path

RESP_HOST = '127.0.0.1'
RESP_PORT = 8001
REQ_HOST = '127.0.0.1'
REQ_PORT = 8000

# Base repo directory (script lives at repo root)
BASE_DIR = Path(__file__).resolve().parent

ADMIN_USER = 'admin@example.com'
ADMIN_PASS = 'admin123'

NEW_USER = 'e2e_user1'
NEW_USER_EMAIL = 'e2e_user1@example.com'
NEW_USER_PASS = 'E2eTestPass123!'

# 1) Login to Response Network as admin
conn = http.client.HTTPConnection(RESP_HOST, RESP_PORT, timeout=10)
login_body = urllib.parse.urlencode({'username': ADMIN_USER, 'password': ADMIN_PASS})
headers = {'Content-Type': 'application/x-www-form-urlencoded'}
conn.request('POST', '/api/v1/auth/login', login_body, headers)
res = conn.getresponse()
print('Response login status:', res.status)
if res.status != 200:
    print(res.read().decode())
    raise SystemExit('Failed to login to Response Network as admin')
login_data = json.loads(res.read().decode())
admin_token = login_data.get('access_token')
print('Got admin token (len):', len(admin_token))
conn.close()

# 2) Create non-admin user
conn = http.client.HTTPConnection(RESP_HOST, RESP_PORT, timeout=10)
user_payload = json.dumps({'username': NEW_USER, 'email': NEW_USER_EMAIL, 'password': NEW_USER_PASS, 'profile_type': 'user'})
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {admin_token}'}
conn.request('POST', '/api/v1/users', user_payload, headers)
res = conn.getresponse()
print('Create user status:', res.status)
print(res.read().decode())
conn.close()

# 3) Trigger export users
conn = http.client.HTTPConnection(RESP_HOST, RESP_PORT, timeout=10)
headers = {'Authorization': f'Bearer {admin_token}'}
conn.request('POST', '/api/v1/users/export/now', '', headers)
res = conn.getresponse()
print('Trigger export status:', res.status)
print(res.read().decode())
conn.close()

# Wait a few seconds for export files to be written
print('Waiting 3 seconds for export to be produced...')
time.sleep(3)

# 4) Run request-network importer script (it uses RESPONSE_EXPORT_PATH env var)
resp_export_dir = str((BASE_DIR / 'response-network' / 'api' / 'exports' / 'users').resolve())
print('Using RESPONSE_EXPORT_PATH =', resp_export_dir)
env = os.environ.copy()
env['RESPONSE_EXPORT_PATH'] = resp_export_dir
# run the importer script from the request-network/api directory so imports resolve
run_cmd = ['python', 'api/scripts/run_users_importer.py']
proc = subprocess.run(run_cmd, env=env, capture_output=True, text=True, cwd=str(BASE_DIR / 'request-network' / 'api'))
print('Importer stdout:')
print(proc.stdout)
print('Importer stderr:')
print(proc.stderr)
# If the importer failed due to module import, try running it from the request-network/api cwd
if 'No module named' in proc.stderr:
    print('Retrying importer with cwd=request-network/api')
    proc = subprocess.run(run_cmd, env=env, capture_output=True, text=True, cwd=os.path.join(os.getcwd(), 'request-network', 'api'))
    print('Importer stdout (retry):')
    print(proc.stdout)
    print('Importer stderr (retry):')
    print(proc.stderr)

# 5) Try login to Request Network with new user
conn = http.client.HTTPConnection(REQ_HOST, REQ_PORT, timeout=10)
login_body = urllib.parse.urlencode({'username': NEW_USER, 'password': NEW_USER_PASS})
headers = {'Content-Type': 'application/x-www-form-urlencoded'}
conn.request('POST', '/api/v1/auth/login', login_body, headers)
res = conn.getresponse()
print('Request-network login status:', res.status)
print(res.read().decode())
conn.close()
