import urllib.request
import urllib.parse
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

FTP_CONFIG = {
    "type": "ftp",
    "host": "192.168.214.139", # Central FTP Server
    "user": "ftp_admin",
    "password": "123456",
    "path": "upload"
}

def get_token():
    url = f"{BASE_URL}/auth/access-token"
    data = urllib.parse.urlencode({
        "username": USERNAME,
        "password": PASSWORD
    }).encode()
    
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result["access_token"]
    except Exception as e:
        print(f"Failed to login: {e}")
        sys.exit(1)

def transform_config(setting_name, config):
    # Adjust config format if necessary based on endpoint expectations
    # The endpoint expects the dict directly as the body
    return config

def update_setting(token, endpoint, config):
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(config).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print(f"✅ Successfully updated {endpoint}")
            else:
                print(f"⚠️ Unexpected status {response.code} for {endpoint}")
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to update {endpoint}: {e} - {e.read().decode()}")
    except Exception as e:
        print(f"❌ Error updating {endpoint}: {e}")

def main():
    print("🔐 Authenticating...")
    token = get_token()
    print("✅ Authenticated")
    
    print(f"\n⚙️ Configuring Import Settings (FTP: {FTP_CONFIG['host']})...")
    update_setting(token, "/settings/system/import_config", FTP_CONFIG)
    
    print(f"\n⚙️ Configuring Export Settings (FTP: {FTP_CONFIG['host']})...")
    update_setting(token, "/settings/system/export_config", FTP_CONFIG)
    
    print("\n✨ Configuration Complete!")

if __name__ == "__main__":
    main()
