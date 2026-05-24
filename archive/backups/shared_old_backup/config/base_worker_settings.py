"""
Base configuration for worker settings. These settings are used during initial setup
and as fallback when database settings are not available.
"""
from typing import Dict
from pathlib import Path

# Base paths
BASE_EXPORT_PATH = Path("/exports")
BASE_IMPORT_PATH = Path("/imports")

class BaseWorkerSettings:
    """Base settings for workers that are required for initial setup."""
    
    @staticmethod
    def get_response_base_settings() -> Dict:
        """Get base settings for response network workers."""
        return {
            "export_settings": {
                "worker_type": "export_settings",
                "storage_type": "local",
                "storage_path": str(BASE_EXPORT_PATH / "settings"),
                "schedule_expression": "*/1 * * * *",  # every 1 minute
                "is_active": True,
                "description": "Base configuration for settings export"
            }
        }
    
    @staticmethod
    def get_request_base_settings() -> Dict:
        """Get base settings for request network workers."""
        return {
            "import_settings": {
                "worker_type": "import_settings",
                "storage_type": "local",
                "storage_path": str(BASE_IMPORT_PATH / "settings"),
                "is_active": True,
                "description": "Base configuration for settings import"
            }
        }