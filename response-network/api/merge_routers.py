import os
import shutil
import glob

api_dir = "/home/docker/my-distributed-app/the_first-1/response-network/api"
router_dir = os.path.join(api_dir, "router")
routers_dir = os.path.join(api_dir, "routers")

if not os.path.exists(router_dir):
    print("router_dir does not exist")
    exit(0)

# Move files
for filename in os.listdir(router_dir):
    src = os.path.join(router_dir, filename)
    dst = os.path.join(routers_dir, filename)
    if filename == "__init__.py":
        continue
    if os.path.isfile(src):
        print(f"Moving {filename}")
        shutil.copy2(src, dst)

# Delete router directory
shutil.rmtree(router_dir)

# Fix imports
python_files = glob.glob(os.path.join(api_dir, "**/*.py"), recursive=True)
for file_path in python_files:
    if "alembic" in file_path:
        continue
    with open(file_path, "r") as f:
        content = f.read()
    
    if "from routers " in content or "from routers." in content or "import routers." in content:
        print(f"Fixing imports in {file_path}")
        content = content.replace("from routers ", "from routers ")
        content = content.replace("from routers.", "from routers.")
        content = content.replace("import routers.", "import routers.")
        with open(file_path, "w") as f:
            f.write(content)

print("Done")
