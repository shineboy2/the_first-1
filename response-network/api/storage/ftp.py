"""FTP storage handler module."""
import os
from typing import Any, Dict, Optional
from pathlib import Path
import ftplib
import tempfile

from .base import StorageHandler

class FTPStorageHandler(StorageHandler):
    """Handler for FTP storage."""
    
    def __init__(self, settings: Dict[str, Any]):
        """Initialize FTP storage handler with settings."""
        super().__init__(settings)
        self.host = settings["host"]
        self.port = settings.get("port") or 21  # Handle None values
        self.username = settings.get("username", "anonymous")
        self.password = settings.get("password", "")
        self.base_path = settings.get("base_path", "/")
        self.use_tls = settings.get("use_tls", False)
    
    def _get_connection(self) -> ftplib.FTP:
        """Get FTP connection."""
        if self.use_tls:
            ftp = ftplib.FTP_TLS()
        else:
            ftp = ftplib.FTP()
            
        ftp.connect(self.host, self.port)
        ftp.login(self.username, self.password)
        
        if self.use_tls:
            ftp.prot_p()  # Switch to secure data connection
            
        return ftp
    
    async def test_connection(self) -> bool:
        """Test FTP connection and write access."""
        try:
            with self._get_connection() as ftp:
                # Try to create and remove a test directory
                test_dir = f"{self.base_path}/.test_write"
                try:
                    ftp.mkd(test_dir)
                    ftp.rmd(test_dir)
                except ftplib.error_perm:
                    pass  # Directory might already exist or we might not have permission
                return True
        except (ftplib.error_perm, ftplib.error_proto, OSError):
            return False
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to FTP server."""
        try:
            with self._get_connection() as ftp:
                # Create remote directories if needed
                current_dir = self.base_path
                for part in Path(remote_path).parent.parts:
                    current_dir = f"{current_dir}/{part}"
                    try:
                        ftp.mkd(current_dir)
                    except ftplib.error_perm:
                        pass  # Directory might already exist
                
                # Upload file
                with open(local_path, 'rb') as f:
                    ftp.storbinary(f'STOR {self.base_path}/{remote_path}', f)
                return True
        except (ftplib.error_perm, ftplib.error_proto, OSError):
            return False
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from FTP server."""
        try:
            with self._get_connection() as ftp:
                # Create local directories if needed
                os.makedirs(Path(local_path).parent, exist_ok=True)
                
                # Download file
                with open(local_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {self.base_path}/{remote_path}', f.write)
                return True
        except (ftplib.error_perm, ftplib.error_proto, OSError):
            return False
    
    async def list_files(self, path: str) -> list[str]:
        """List files in FTP path."""
        try:
            with self._get_connection() as ftp:
                files = []
                def _list_recursive(current_path: str):
                    try:
                        for name, facts in ftp.mlsd(f"{self.base_path}/{current_path}"):
                            if name in ('.', '..'):
                                continue
                            full_path = f"{current_path}/{name}" if current_path else name
                            if facts['type'] == 'file':
                                files.append(full_path)
                            elif facts['type'] == 'dir':
                                _list_recursive(full_path)
                    except ftplib.error_perm:
                        pass  # Directory might not exist
                
                _list_recursive(path)
                return files
        except (ftplib.error_perm, ftplib.error_proto, OSError):
            return []
    
    async def delete_file(self, path: str) -> bool:
        """Delete file from FTP server."""
        try:
            with self._get_connection() as ftp:
                ftp.delete(f"{self.base_path}/{path}")
                return True
        except (ftplib.error_perm, ftplib.error_proto, OSError):
            return False