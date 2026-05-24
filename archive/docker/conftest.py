"""
Root conftest.py for pytest
Ensures that shared, core, and API modules are properly importable
"""
import sys
from pathlib import Path

# Get the project root
PROJECT_ROOT = Path(__file__).parent.resolve()

# Add project root to sys.path so that shared and core modules are importable
# This ensures both local development and Docker environments work
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Add API directories for imports
api_dirs = [
    PROJECT_ROOT / "request-network" / "api",
    PROJECT_ROOT / "response-network" / "api",
]

for api_dir in api_dirs:
    api_path = str(api_dir)
    if api_path not in sys.path:
        sys.path.insert(0, api_path)
