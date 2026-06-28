import os
import sys

# Insert /app into sys.path to resolve imports
sys.path.insert(0, '/app')

from routers.request_types_router import _load_request_types, _filter_by_user_access
from models.user import User

try:
    print("Loading request types from disk...")
    types = _load_request_types()
    print("Loaded types:", type(types), len(types) if types else 0)
    if types:
        print("First type name:", types[0].get("name"))

    print("\nFiltering for admin user...")
    admin_user = User(username="admin", profile_type="admin", allowed_request_types=[], blocked_request_types=[])
    filtered = _filter_by_user_access(types, admin_user)
    print("Filtered types:", len(filtered) if filtered else 0)
    if filtered:
        print("First filtered type name:", filtered[0].get("name"))
except Exception as e:
    import traceback
    traceback.print_exc()

