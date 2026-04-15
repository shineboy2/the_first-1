import os
import json
import logging
import ftplib
import io
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.settings import Settings

logger = logging.getLogger(__name__)

class ImportStorageService:
    @staticmethod
    def get_import_config(db: Session, resource_type: str = None) -> dict:
        """Fetch import configuration from database settings.
        Maps resource_type to specific config keys:
        - 'results' -> 'result_import_config'
        - 'settings' -> 'settings_import_config'
        - 'users' -> 'user_import_config' (fallback to 'import_config')
        """
        # Map resource types to config keys
        config_key = "import_config"  # Default fallback
        if resource_type == "results":
            config_key = "result_import_config"
        elif resource_type == "settings":
            config_key = "settings_import_config"
        elif resource_type == "users":
            config_key = "user_import_config"
        
        result = db.execute(select(Settings).where(Settings.key == config_key))
        setting = result.scalar_one_or_none()
        
        # Fallback to generic 'import_config' if specific one not found
        if not setting and config_key != "import_config":
            result = db.execute(select(Settings).where(Settings.key == "import_config"))
            setting = result.scalar_one_or_none()
            
        if not setting or not setting.value:
            return None
        return setting.value

    @staticmethod
    def read_latest_file(db: Session, resource_type: str) -> dict:
        """
        Read the latest import file for a resource type (e.g., 'users').
        Abstraacts away Local vs FTP logic.
        """
        config = ImportStorageService.get_import_config(db, resource_type)
        if not config:
            logger.info(f"Skipping import for {resource_type}: Import configuration missing. Waiting for admin to configure via API.")
            return None

        import_type = config.get("storage_type", "local")
        
        if import_type == "local":
            base_path = Path(config.get("local_path", "/app/imports"))
            file_path = base_path / resource_type / "latest.json"
            
            if not file_path.exists():
                logger.info(f"No import file found at {file_path}")
                return None
                
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read local import file {file_path}: {e}")
                return None
        
        elif import_type == "ftp":
            host = config.get("ftp_host")
            user = config.get("ftp_user")
            passwd = config.get("ftp_password")
            port = config.get("ftp_port", 21)
            remote_path = config.get("ftp_path", f"/{resource_type}")
            use_tls = config.get("ftp_use_tls", False)
            
            if not host:
                logger.error(f"FTP host missing in import_config for {resource_type}")
                return None
            
            try:
                bio = io.BytesIO()
                
                # Connect to FTP server
                if use_tls:
                    ftp = ftplib.FTP_TLS()
                    ftp.connect(host, port)
                    ftp.login(user=user, passwd=passwd)
                    ftp.prot_p()  # Enable encryption
                else:
                    ftp = ftplib.FTP()
                    ftp.connect(host, port)
                    ftp.login(user=user, passwd=passwd)
                
                try:
                    ftp.cwd(remote_path)
                except:
                    pass
                
                # Dynamic Latest Resolution
                # List all files
                files = ftp.nlst()
                
                extension = ".jsonl" if resource_type == "results" else ".json"
                candidates = [f for f in files if f.startswith(f"{resource_type}_") and f.endswith(extension)]
                
                if not candidates:
                    # Fallback to latest.json ONLY if explicitly checking for it or if no timestamped files
                    if "latest.json" in files and resource_type not in ["settings"]: 
                        # 'settings' specifically collides with user export, so we strictly avoid latest.json for it
                        target_file = "latest.json"
                    else:
                        logger.info(f"No entry found for {resource_type} in {remote_path}")
                        try:
                            ftp.quit()
                        except:
                            ftp.close()
                        return None
                else:
                    # Sort by name (timestamp ISO format sorts correctly)
                    candidates.sort()
                    target_file = candidates[-1]

                logger.info(f"Downloading latest {resource_type} file: {target_file}")
                ftp.retrbinary(f"RETR {target_file}", bio.write)
                
                try:
                    ftp.quit()
                except:
                    ftp.close()
                
                bio.seek(0)
                if resource_type == "results":
                     lines = bio.getvalue().decode('utf-8').splitlines()
                     return [json.loads(line) for line in lines if line.strip()]
                else:
                     return json.load(bio)
            except Exception as e:
                logger.error(f"FTP Download failed from {host}:{remote_path}: {e}")
                return None
        
        else:
            logger.error(f"Unknown import type: {import_type}")
            return None
