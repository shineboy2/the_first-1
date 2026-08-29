import sys
print("Python path:")
for p in sys.path:
    print(f"  {p}")

print("\nTrying to import schemas:")
try:
    import schemas
    print(f"  schemas found at: {schemas.__file__}")
    print(f"  schemas is package: {hasattr(schemas, '__path__')}")
except ImportError as e:
    print(f"  ImportError: {e}")
