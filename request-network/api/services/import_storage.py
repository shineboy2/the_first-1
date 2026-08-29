import os
import json
import logging
import ftplib
import hashlib
import io
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.settings import Settings
from models.file_import_state import FileImportState
from core.encryption import decrypt_data

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
        elif resource_type == "request_types":
            config_key = "request_types_import_config"
        
        result = db.execute(select(Settings).where(Settings.key == config_key))
        setting = result.scalar_one_or_none()
        
        # Fallback to generic 'import_config' if specific one not found
        if not setting and config_key != "import_config":
            result = db.execute(select(Settings).where(Settings.key == "import_config"))
            setting = result.scalar_one_or_none()
            
        if not setting or not setting.value:
            return None, None
        return setting.value

    @staticmethod
    def get_next_unprocessed_file(db: Session, resource_type: str) -> tuple:
        """
        Read the oldest unprocessed import file, locking it via FileImportState.
        Returns: (data, filename, metadata, meta_filename) or (None, None, None, None)
        """
        config = ImportStorageService.get_import_config(db, resource_type)
        if not config:
            logger.info(f"Skipping import for {resource_type}: Import configuration missing.")
            return None, None, None, None

        import_type = config.get("storage_type", config.get("type", "local"))
        worker_id = os.environ.get("HOSTNAME", "unknown_worker")
        
        target_file = None
        files = []
        extension = ".jsonl" if resource_type in ["requests", "results"] else ".json"
        
        # 1. Fetch file list
        if import_type == "local":
            base_path = Path(config.get("local_path", config.get("path", "/app/imports")))
            res_dir = base_path / resource_type
            if not res_dir.exists():
                return None, None, None, None
            files = [f.name for f in res_dir.iterdir() if f.is_file()]
            
        elif import_type == "ftp":
            host = None; user = None; passwd = None; port = 21; use_tls = False
            remote_path = config.get("ftp_path", config.get("path", f"/{resource_type}"))
            
            ftp_profile_id = config.get("ftp_profile_id")
            if ftp_profile_id:
                from models.ftp_profile import FTPProfile
                ftp_profile = db.execute(select(FTPProfile).where(FTPProfile.id == ftp_profile_id, FTPProfile.is_active == True)).scalar_one_or_none()
                if ftp_profile:
                    host = ftp_profile.host; user = ftp_profile.username; passwd = ftp_profile.password
                    port = ftp_profile.port or 21; use_tls = ftp_profile.use_tls
            
            if not host:
                host = config.get("ftp_host", config.get("host"))
                user = config.get("ftp_user", config.get("user"))
                passwd = config.get("ftp_password", config.get("password"))
            
            if not host:
                return None, None, None, None
            
            try:
                ftp = ftplib.FTP_TLS() if use_tls else ftplib.FTP()
                ftp.connect(host, port)
                ftp.login(user=user, passwd=passwd)
                if use_tls:
                    try: ftp.prot_p()
                    except: pass
                try: ftp.cwd(remote_path)
                except: pass
                files = ftp.nlst()
            except Exception as e:
                logger.error(f"FTP connection failed: {e}")
                return None, None, None, None
                
        # 2. Find oldest unprocessed
        candidates = [f for f in files if f.startswith(f"{resource_type}_") and f.endswith(extension) and not f.endswith(".tmp") and not f.endswith(".processed")]
        if not candidates:
            if "latest.json" in files and resource_type not in ["requests", "results", "settings"]:
                candidates = ["latest.json"]
            else:
                if import_type == "ftp":
                    try: ftp.quit()
                    except: ftp.close()
                return None, None, None, None
                
        candidates.sort()
        
        # 3. Check DB for lease and claim
        from datetime import datetime, timedelta
        
        for candidate in candidates:
            # Check if locked
            state = db.query(FileImportState).filter(FileImportState.filename == candidate).with_for_update(skip_locked=True).first()
            now = datetime.utcnow()
            
            if state:
                if state.status == "PROCESSED":
                    continue
                if state.status == "FAILED":
                    continue
                if state.status == "PROCESSING" and state.lease_until and state.lease_until > now:
                    continue # Locked by someone else
            else:
                state = FileImportState(filename=candidate, resource_type=resource_type)
                db.add(state)
            
            # Claim it
            state.status = "PROCESSING"
            state.worker_id = worker_id
            state.lease_until = now + timedelta(minutes=10)
            db.commit()
            
            target_file = candidate
            break
            
        if not target_file:
            if import_type == "ftp":
                try: ftp.quit()
                except: ftp.close()
            return None, None, None, None

        logger.info(f"Downloading claimed file {target_file}")
        
        # 4. Download file and metadata
        raw_data = None
        metadata = None
        meta_filename = target_file.replace(extension, ".meta.json")
        
        if import_type == "local":
            file_path = res_dir / target_file
            meta_path = res_dir / meta_filename
            try:
                with open(file_path, "rb") as f:
                    raw_data = f.read()
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
            except Exception as e:
                logger.error(f"Local read failed: {e}")
                return None, None, None, None
        else:
            try:
                bio = io.BytesIO()
                meta_bio = io.BytesIO()
                ftp.retrbinary(f"RETR {target_file}", bio.write)
                bio.seek(0)
                raw_data = bio.getvalue()
                
                if meta_filename in files:
                    ftp.retrbinary(f"RETR {meta_filename}", meta_bio.write)
                    meta_bio.seek(0)
                    metadata = json.loads(meta_bio.getvalue().decode('utf-8'))
                    
                try: ftp.quit()
                except: ftp.close()
            except Exception as e:
                logger.error(f"FTP DL failed: {e}")
                return None, None, None, None
                
        # 5. Checksum Strict Validation
        if metadata and "checksum" in metadata:
            expected = metadata["checksum"]
            actual = hashlib.sha256(raw_data).hexdigest()
            if actual != expected:
                logger.error(f"CHECKSUM MISMATCH for {target_file}: expected {expected} got {actual}")
                state = db.query(FileImportState).filter(FileImportState.filename == target_file).first()
                if state:
                    state.status = "FAILED"
                    db.commit()
                # Quarantine the file physically
                ImportStorageService.quarantine_file(db, resource_type, target_file, meta_filename if metadata else None)
                return None, None, None, None
                
        # 6. Parse and return
        try:
            if 'request-network' in filepath:
                from core.encryption import decrypt_data
                decrypted_data = decrypt_data(raw_data)
                if extension == ".jsonl":
                    lines = decrypted_data.decode("utf-8").splitlines()
                    data = [json.loads(line) for line in lines if line.strip()]
                else:
                    data = json.loads(decrypted_data.decode("utf-8"))
            else:
                if extension == ".jsonl":
                    lines = raw_data.decode("utf-8").splitlines()
                    data = [json.loads(line) for line in lines if line.strip()]
                else:
                    data = json.loads(raw_data.decode("utf-8"))
            return data, target_file, metadata, meta_filename if metadata else None
        except Exception as e:
            logger.error(f"Parse failed {target_file}: {e}")
            return None, None, None, None

    @staticmethod
    def archive_file(db: Session, resource_type: str, filename: str, meta_filename: str = None):
        state = db.query(FileImportState).filter(FileImportState.filename == filename).first()
        if state:
            state.status = "PROCESSED"
            db.commit()

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

    @staticmethod
    def quarantine_file(db: Session, resource_type: str, filename: str, meta_filename: str = None):
        config = ImportStorageService.get_import_config(db, resource_type)
        if not config: return
        import_type = config.get("storage_type", config.get("type", "local"))
        
        if import_type == "local":
            base_path = Path(config.get("local_path", config.get("path", "/app/imports")))
            file_path = base_path / resource_type / filename
            if file_path.exists():
                file_path.rename(file_path.with_name(filename + ".failed"))
            if meta_filename:
                meta_path = base_path / resource_type / meta_filename
                if meta_path.exists():
                    meta_path.rename(meta_path.with_name(meta_filename + ".failed"))
        elif import_type == "ftp":
            host = config.get("ftp_host", config.get("host"))
            user = config.get("ftp_user", config.get("user"))
            passwd = config.get("ftp_password", config.get("password"))
            remote_path = config.get("ftp_path", config.get("path", f"/{resource_type}"))
            try:
                ftp = ftplib.FTP()
                ftp.connect(host, 21)
                ftp.login(user, passwd)
                try: ftp.cwd(remote_path)
                except: pass
                ftp.rename(filename, filename + ".failed")
                if meta_filename:
                    try: ftp.rename(meta_filename, meta_filename + ".failed")
                    except: pass
                ftp.quit()
            except: pass
