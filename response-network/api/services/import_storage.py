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
        Returns: (data, filename, metadata, meta_filename) or (None, None, None, None)
        """
        config = ImportStorageService.get_import_config(db, resource_type)
        if not config:
            logger.info(f"Skipping import for {resource_type}: Import configuration missing.")
            return None, None, None, None

        import_type = config.get("storage_type", config.get("type", "local"))
        
        if import_type == "local":
            base_path = Path(config.get("local_path", config.get("path", "/app/imports")))
            
            # Find oldest JSONL or JSON
            extension = ".jsonl" if resource_type in ["requests", "results"] else ".json"
            res_dir = base_path / resource_type
            if not res_dir.exists():
                return None, None, None, None
                
            files = [f.name for f in res_dir.iterdir() if f.is_file()]
            candidates = [f for f in files if f.startswith(f"{resource_type}_") and f.endswith(extension) and not f.endswith(".tmp") and not f.endswith(".processed")]
            
            if not candidates:
                if "latest.json" in files and resource_type not in ["requests", "results", "settings"]:
                    target_file = "latest.json"
                else:
                    return None, None, None, None
            else:
                candidates.sort()
                target_file = candidates[0]
                
            file_path = res_dir / target_file
            
            # Check for metadata
            meta_filename = target_file.replace(extension, ".meta.json")
            meta_path = res_dir / meta_filename
            metadata = None
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to read metadata {meta_path}: {e}")
                    
            try:
                if 'request-network' in filepath:
                    # Request network decrypts data
                    from core.encryption import decrypt_data
                    with open(file_path, "rb") as f:
                        raw_data = f.read()
                    decrypted_data = decrypt_data(raw_data)
                    if extension == ".jsonl":
                        lines = decrypted_data.decode("utf-8").splitlines()
                        data = [json.loads(line) for line in lines if line.strip()]
                    else:
                        data = json.loads(decrypted_data.decode("utf-8"))
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        if extension == ".jsonl":
                            data = [json.loads(line) for line in f if line.strip()]
                        else:
                            data = json.load(f)
                return data, target_file, metadata, meta_filename if metadata else None
            except Exception as e:
                logger.error(f"Failed to read local import file {file_path}: {e}")
                return None, None, None, None
                
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
                logger.error(f"FTP host missing in import_config for {resource_type}")
                return None, None, None, None
            
            try:
                bio = io.BytesIO()
                meta_bio = io.BytesIO()
                
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
                    
                files = ftp.nlst()
                
                extension = ".jsonl" if resource_type in ["requests", "results"] else ".json"
                candidates = [f for f in files if f.startswith(f"{resource_type}_") and f.endswith(extension) and not f.endswith(".tmp") and not f.endswith(".processed")]
                
                if not candidates:
                    if "latest.json" in files and resource_type not in ["requests", "results", "settings"]: 
                        target_file = "latest.json"
                    else:
                        try:
                            ftp.quit()
                        except:
                            ftp.close()
                        return None, None, None, None
                else:
                    candidates.sort()
                    target_file = candidates[0]

                logger.info(f"Downloading oldest unprocessed {resource_type} file: {target_file}")
                ftp.retrbinary(f"RETR {target_file}", bio.write)
                
                # Try to download metadata
                meta_filename = target_file.replace(extension, ".meta.json")
                metadata = None
                if meta_filename in files:
                    try:
                        ftp.retrbinary(f"RETR {meta_filename}", meta_bio.write)
                        meta_bio.seek(0)
                        metadata = json.loads(meta_bio.getvalue().decode('utf-8'))
                    except Exception as e:
                        logger.error(f"Failed to read metadata {meta_filename}: {e}")
                
                try:
                    ftp.quit()
                except:
                    ftp.close()
                
                bio.seek(0)
                
                if 'request-network' in filepath:
                    from core.encryption import decrypt_data
                    raw_data = bio.getvalue()
                    decrypted_data = decrypt_data(raw_data)
                    if extension == ".jsonl":
                        lines = decrypted_data.decode('utf-8').splitlines()
                        data = [json.loads(line) for line in lines if line.strip()]
                    else:
                        data = json.loads(decrypted_data.decode('utf-8'))
                else:
                    if extension == ".jsonl":
                        lines = bio.getvalue().decode('utf-8').splitlines()
                        data = [json.loads(line) for line in lines if line.strip()]
                    else:
                        data = json.load(bio)
                        
                return data, target_file, metadata, meta_filename if metadata else None
                    
            except Exception as e:
                logger.error(f"FTP Download failed from {host}:{remote_path}: {e}")
                return None, None, None, None
        
        else:
            logger.error(f"Unknown import type: {import_type}")
            return None, None, None, None

    @staticmethod
    def archive_file(db: Session, resource_type: str, filename: str, meta_filename: str = None):
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
            if meta_filename:
                meta_path = base_path / resource_type / meta_filename
                if meta_path.exists():
                    meta_path.rename(meta_path.with_name(meta_filename + ".processed"))
                
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
                if meta_filename:
                    try:
                        ftp.rename(meta_filename, meta_filename + ".processed")
                    except Exception as e:
                        logger.error(f"Failed to archive meta file {meta_filename}: {e}")
                
                try:
                    ftp.quit()
                except:
                    ftp.close()
            except Exception as e:
                logger.error(f"Failed to archive FTP file {filename}: {e}")
