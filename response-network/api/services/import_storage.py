import os
import json
import logging
import ftplib
import io
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.settings import Settings
from models.ftp_profile import FTPProfile

logger = logging.getLogger(__name__)

class ImportStorageService:
    @staticmethod
    def get_import_config(db: Session, resource_type: str = None) -> dict:
        """Fetch import configuration from database settings."""
        # Map resource type to specific config keys
        key = "import_config"
        if resource_type == "requests":
            key = "request_import_config"
        
        result = db.execute(select(Settings).where(Settings.key == key))
        setting = result.scalar_one_or_none()
        
        # Fallback to generic config if specific not found
        if not setting and key != "import_config":
             result = db.execute(select(Settings).where(Settings.key == "import_config"))
             setting = result.scalar_one_or_none()

        if not setting or not setting.value:
            return None, None
        return setting.value

    @staticmethod
    def get_next_unprocessed_file(db: Session, resource_type: str) -> tuple:
        """
        Read the oldest unprocessed import file.
        Returns: (data, filename) or (None, None)
        """
        """
        Read the latest import file for a resource type (e.g., 'requests').
        Abstraacts away Local vs FTP logic.
        """
        config = ImportStorageService.get_import_config(db, resource_type)
        if not config:
            logger.info(f"Skipping import for {resource_type}: Import configuration missing. Waiting for admin to configure via API.")
            return None, None

        # Mapping field names from admin_exports.py schema
        import_type = config.get("storage_type", config.get("type", "local"))
        
        if import_type == "local":
            base_path = Path(config.get("local_path", config.get("path", "/app/imports")))
            file_path = base_path / resource_type / "latest.json"
            
            if not file_path.exists():
                logger.info(f"No import file found at {file_path}")
                return None, None
                
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f), file_path.name
            except Exception as e:
                logger.error(f"Failed to read local import file {file_path}: {e}")
                return None, None
        
        elif import_type == "ftp":
            host = None
            user = None
            passwd = None
            port = 21
            use_tls = False
            remote_path = config.get("ftp_path", config.get("path", f"/{resource_type}"))
            
            ftp_profile_id = config.get("ftp_profile_id")
            if ftp_profile_id:
                result = db.execute(select(FTPProfile).where(FTPProfile.id == ftp_profile_id, FTPProfile.is_active == True))
                ftp_profile = result.scalar_one_or_none()
                if ftp_profile:
                    host = ftp_profile.host
                    user = ftp_profile.username
                    passwd = ftp_profile.password
                    port = ftp_profile.port or 21
                    use_tls = ftp_profile.use_tls
            
            if not host:
                host = config.get("ftp_host", config.get("host"))
                user = config.get("ftp_user", config.get("user"))
                passwd = config.get("ftp_password", config.get("password"))
            
            if not host:
                logger.error(f"FTP host missing in import_config for {resource_type}")
                return None, None
            
            try:
                bio = io.BytesIO()
                if use_tls:
                    ftp = ftplib.FTP_TLS()
                else:
                    ftp = ftplib.FTP()
                    
                with ftp:
                    ftp.connect(host, port)
                    ftp.login(user=user, passwd=passwd)
                    try:
                        ftp.cwd(remote_path)
                    except:
                        pass
                    
                    # Dynamic Latest Resolution
                    # List all files
                    files = ftp.nlst()
                    
                    # Filter for resource type (e.g. 'requests_') and exclude 'latest.json' if needed
                    # Request Network exports 'requests_2025...jsonl' (Note: JSONL, not JSON)
                    # We might need to handle .jsonl extension specifically or generically
                    
                    # Request Network exports as .jsonl
                    extension = ".jsonl" if resource_type == "requests" else ".json"
                    
                    candidates = [f for f in files if f.startswith(f"{resource_type}_") and f.endswith(extension) and not f.endswith(".tmp") and not f.endswith(".processed")]
                    
                    if not candidates:
                        # Fallback for legacy or static files
                        if "latest.json" in files and resource_type not in ["requests", "settings"]: 
                            target_file = "latest.json"
                        else:
                            logger.info(f"No entry found for {resource_type} in {remote_path}")
                            return None, None
                    else:
                        # Sort by name (timestamp ISO format sorts correctly)
                        candidates.sort()
                        target_file = candidates[0]

                    logger.info(f"Downloading oldest unprocessed {resource_type} file: {target_file}")
                    ftp.retrbinary(f"RETR {target_file}", bio.write)
                
                bio.seek(0)
                
                # Handle JSON vs JSONL
                if resource_type == "requests":
                    # For JSONL, we return a list of dicts
                    # The ImportStorageService usually returns a single dict (for json).
                    # We should adapt the caller or this method.
                    # Given the abstraction, it's safer to return parsed data.
                    # For JSONL:
                    lines = bio.getvalue().decode('utf-8').splitlines()
                    return [json.loads(line) for line in lines if line.strip()], target_file
                else:
                    return json.load(bio), target_file
                    
            except Exception as e:
                logger.error(f"FTP Download failed from {host}:{remote_path}: {e}")
                return None, None
        
        else:
            logger.error(f"Unknown import type: {import_type}")
            return None, None

    @staticmethod
    def archive_file(db: Session, resource_type: str, filename: str):
        config = ImportStorageService.get_import_config(db, resource_type)
        if not config:
            return
        
        import_type = config.get("storage_type", config.get("type", "local"))
        
        if import_type == "local":
            base_path = Path(config.get("local_path", config.get("path", "/app/imports")))
            file_path = base_path / resource_type / filename
            if file_path.exists():
                file_path.rename(file_path.with_name(filename + ".processed"))
                logger.info(f"Archived local file: {filename}")
                
        elif import_type == "ftp":
            host = None
            user = None
            passwd = None
            port = 21
            use_tls = False
            remote_path = config.get("ftp_path", config.get("path", f"/{resource_type}"))
            
            ftp_profile_id = config.get("ftp_profile_id")
            if ftp_profile_id:
                from models.ftp_profile import FTPProfile
                result = db.execute(select(FTPProfile).where(FTPProfile.id == ftp_profile_id, FTPProfile.is_active == True))
                ftp_profile = result.scalar_one_or_none()
                if ftp_profile:
                    host = ftp_profile.host
                    user = ftp_profile.username
                    passwd = ftp_profile.password
                    port = ftp_profile.port or 21
                    use_tls = ftp_profile.use_tls
                    
            if not host:
                host = config.get("ftp_host", config.get("host"))
                user = config.get("ftp_user", config.get("user"))
                passwd = config.get("ftp_password", config.get("password"))
                
            if not host:
                return
                
            try:
                if use_tls:
                    ftp = ftplib.FTP_TLS()
                    ftp.connect(host, port)
                    ftp.login(user=user, passwd=passwd)
                    try:
                        ftp.prot_p()
                    except:
                        pass
                else:
                    ftp = ftplib.FTP()
                    ftp.connect(host, port)
                    ftp.login(user=user, passwd=passwd)
                
                try:
                    ftp.cwd(remote_path)
                except:
                    pass
                    
                ftp.rename(filename, filename + ".processed")
                logger.info(f"Archived FTP file: {filename}")
                
                try:
                    ftp.quit()
                except:
                    ftp.close()
            except Exception as e:
                logger.error(f"Failed to archive FTP file {filename}: {e}")
