import os
import re

def fix_imports(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='cp1252') as f:
                            content = f.read()
                    except:
                        print(f"Skipping {file_path} - encoding issue")
                        continue
                
                # Convert relative imports to absolute and fix any direct imports
                new_content = content
                
                # Convert relative imports (both single and double dots)
                new_content = re.sub(
                    r'from \.{1,2}([^ ]+) import',
                    lambda m: f'from response_network.api.{m.group(1).lstrip(".")} import',
                    new_content
                )
                
                # Fix any remaining relative imports (single dot)
                new_content = re.sub(
                    r'from \. import',
                    'from response_network.api import',
                    new_content
                )
                
                if new_content != content:
                    print(f"Fixing imports in {file_path}")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

if __name__ == "__main__":
    api_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Fixing imports in {api_dir}")
    fix_imports(api_dir)