"""Base storage handler module."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class StorageHandler(ABC):
    """Base class for storage handlers."""
    
    def __init__(self, settings: Dict[str, Any]):
        """Initialize storage handler with settings."""
        self.settings = settings
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to storage."""
        pass
    
    @abstractmethod
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to storage."""
        pass
    
    @abstractmethod
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from storage."""
        pass
    
    @abstractmethod
    async def list_files(self, path: str) -> list[str]:
        """List files in storage path."""
        pass
    
    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """Delete file from storage."""
        pass
