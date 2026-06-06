"""
Storage service for handling file exports to different destinations.
"""
from pathlib import Path
from typing import BinaryIO, Union
import tempfile

from core.config import settings
from storage.local import LocalStorageHandler
from storage.ftp import FTPStorageHandler
from core.encryption import encrypt_data


class ExportStorageService:
    """Service for saving export files to configured destination."""
    
    @staticmethod
    async def save_export_file(filename: str, data: bytes, config: dict = None) -> str:
        """
        Save export file to configured destination.
        
        Args:
            filename: Name of the file to save
            data: File content as bytes
            config: Optional configuration dictionary (overrides static settings)
            
        Returns:
            Path or URL where file was saved
        """
        # Encrypt the data before saving
        data = encrypt_data(data)

        # Prioritize dynamic config if provided
        if config:
            export_type = config.get("type", "local")
            if export_type == "ftp":
                return await ExportStorageService._save_to_ftp_dynamic(filename, data, config)
            else:
                return await ExportStorageService._save_to_local_dynamic(filename, data, config)

        # Fallback to static settings (only local for request network usually, but could be extended)
        return await ExportStorageService._save_to_local(filename, data)
    
    @staticmethod
    async def _save_to_local(filename: str, data: bytes) -> str:
        """Save file to local file system."""
        handler = LocalStorageHandler({"base_path": settings.EXPORT_DIR})
        
        # Write to temp file first
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        
        # Upload (copy) to destination
        await handler.upload_file(tmp_path, filename)
        
        # Clean up temp file
        Path(tmp_path).unlink()
        
        return str(Path(settings.EXPORT_DIR) / filename)

    @staticmethod
    async def _save_to_local_dynamic(filename: str, data: bytes, config: dict) -> str:
        """Save to local using dynamic config."""
        path = config.get("path", settings.EXPORT_DIR)
        handler = LocalStorageHandler({"base_path": path})
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        
        await handler.upload_file(tmp_path, filename)
        Path(tmp_path).unlink()
        
        return str(Path(path) / filename)

    @staticmethod
    async def _save_to_ftp_dynamic(filename: str, data: bytes, config: dict) -> str:
        """Save to FTP using dynamic config."""
        ftp_settings = {
            "host": config.get("host"),
            "port": config.get("port", 21),
            "username": config.get("user"),
            "password": config.get("password"),
            "base_path": config.get("path", "/"),
            "use_tls": config.get("use_tls", False),
        }
        
        handler = FTPStorageHandler(ftp_settings)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        
        await handler.upload_file(tmp_path, filename)
        Path(tmp_path).unlink()
        
        return f"ftp://{config.get('host')}{config.get('path')}/{filename}"
