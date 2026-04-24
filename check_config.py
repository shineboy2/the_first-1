#!/usr/bin/env python3
import subprocess
import json

# First, let's check the bootstrap config to see what was configured
script = '''
import sys
sys.path.insert(0, '/app')
from api.core.config import settings
from api.services.import_storage import ImportStorageService
from api.models.database import get_db_sync

# Get DB connection
db = next(get_db_sync())

# Get import config
config = ImportStorageService.get_import_config(db, 'user_import')
print(json.dumps(config, indent=2, default=str))
import json
'''

cmd = [
    'sshpass', '-p', '1',
    'ssh', '-o', 'StrictHostKeyChecking=no',
    'request@192.168.214.146',
    f"docker exec request-api python3 -c \"{script}\""
]

result = subprocess.run(' '.join(cmd), shell=True, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("ERROR:", result.stderr)
