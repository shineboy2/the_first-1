#!/usr/bin/env python3
"""
Trigger User Import Manually
This script directly calls the import task without using Celery CLI.
"""
import sys
from pathlib import Path

# Add API directory to path
api_dir = Path(__file__).parent / "api"
sys.path.insert(0, str(api_dir))

from workers.tasks.users_importer import import_users_from_response_network

if __name__ == "__main__":
    print("🚀 Triggering user import from Response Network...")
    result = import_users_from_response_network()
    print(f"\n✅ Result: {result}")
