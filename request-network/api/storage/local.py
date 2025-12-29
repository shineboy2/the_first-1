"""Local storage handler module."""
import os
import shutil
from typing import Any, Dict, Optional
from pathlib import Path

from .base import StorageHandler

class LocalStorageHandler(StorageHandler):
    """Handler for local file system storage."""
    
    def __init__(self, settings: Dict[str, Any]):
        """Initialize local storage handler with settings."""
        super().__init__(settings)
        self.base_path = Path(settings["base_path"])
        
        # Ensure base path exists
        os.makedirs(self.base_path, exist_ok=True)
    
    async def test_connection(self) -> bool:
        """Test if base path exists and is writable."""
        try:
            # Create a temp file to test write access
            test_file = self.base_path / ".test_write"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except (OSError, IOError):
            return False
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Copy file to local storage path."""
        try:
            dest_path = self.base_path / remote_path
            os.makedirs(dest_path.parent, exist_ok=True)
            shutil.copy2(local_path, dest_path)
            return True
        except (OSError, IOError):
            return False
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Copy file from local storage path."""
        try:
            src_path = self.base_path / remote_path
            os.makedirs(Path(local_path).parent, exist_ok=True)
            shutil.copy2(src_path, local_path)
            return True
        except (OSError, IOError):
            return False
    
    async def list_files(self, path: str) -> list[str]:
        """List files in local storage path."""
        try:
            search_path = self.base_path / path
            if not search_path.exists():
                return []
                
            files = []
            for p in search_path.rglob("*"):
                if p.is_file():
                    files.append(str(p.relative_to(self.base_path)))
            return files
        except (OSError, IOError):
            return []
    
    async def delete_file(self, path: str) -> bool:
        """Delete file from local storage."""
        try:
            file_path = self.base_path / path
            if file_path.exists():
                file_path.unlink()
            return True
        except (OSError, IOError):
            return False
