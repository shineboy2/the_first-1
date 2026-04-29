from pathlib import Path
import sys

print(f"Current working directory: {Path.cwd()}")
print(f"\nsys.path:")
for p in sys.path[:10]:
    print(f"  {p}")

shared_path = Path("c:/Users/win/the_first/shared/database/base.py")
print(f"\nShared path exists: {shared_path.exists()}")
print(f"Shared path absolute: {shared_path.absolute()}")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print(f"\nAfter sys.path.insert:")
print(f"  Added: {Path(__file__).parent.parent.parent}")

try:
    from .shared.database.base import BaseModel, TimestampMixin, UUIDMixin
    print("\nImport successful!")
except Exception as e:
    print(f"\nImport failed: {e}")
