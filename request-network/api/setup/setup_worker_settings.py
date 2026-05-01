"""
Setup script for request network worker settings.
This script creates the base configuration file and directories.
"""
import json
from pathlib import Path

from shared.config.base_worker_settings import BaseWorkerSettings, BASE_IMPORT_PATH

def setup_base_worker_settings():
    """Setup base worker settings configuration."""
    # Create base import directories
    BASE_IMPORT_PATH.mkdir(parents=True, exist_ok=True)
    
    base_settings = BaseWorkerSettings.get_request_base_settings()
    for settings_dict in base_settings.values():
        Path(settings_dict["storage_path"]).mkdir(parents=True, exist_ok=True)
    
    # Write base settings to config file
    config_path = Path("config/worker_settings.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w") as f:
        json.dump(base_settings, f, indent=2)

if __name__ == "__main__":
    setup_base_worker_settings()