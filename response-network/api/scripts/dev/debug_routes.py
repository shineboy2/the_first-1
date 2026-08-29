import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from main import app

print(f"{'METHOD':<10} {'PATH':<50} {'NAME':<30}")
print("-" * 90)
for route in app.routes:
    if hasattr(route, "methods"):
        methods = ", ".join(route.methods)
        print(f"{methods:<10} {route.path:<50} {route.name:<30}")
