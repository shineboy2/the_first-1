import re
import sys

def patch_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # 1. Rename read_latest_file to get_next_unprocessed_file and return tuple
    content = content.replace('def read_latest_file(db: Session, resource_type: str) -> dict:', 
                              'def get_next_unprocessed_file(db: Session, resource_type: str) -> tuple:\n        """\n        Read the oldest unprocessed import file.\n        Returns: (data, filename) or (None, None)\n        """')
    
    # 2. Change return None to return None, None
    content = re.sub(r'return None(\s*)', r'return None, None\1', content)
    
    # 3. Change candidates filter to exclude .processed and .tmp
    content = content.replace('candidates = [f for f in files if f.startswith(f"{resource_type}_") and f.endswith(extension)]',
                              'candidates = [f for f in files if f.startswith(f"{resource_type}_") and f.endswith(extension) and not f.endswith(".tmp") and not f.endswith(".processed")]')
                              
    # 4. Change latest to oldest
    content = content.replace('target_file = candidates[-1]', 'target_file = candidates[0]')
    content = content.replace('Downloading latest', 'Downloading oldest unprocessed')
    
    # 5. Fix returns to include target_file
    content = content.replace('return json.loads(decrypted_data.decode("utf-8"))',
                              'return json.loads(decrypted_data.decode("utf-8")), target_file')
    content = content.replace('return [json.loads(line) for line in lines if line.strip()]',
                              'return [json.loads(line) for line in lines if line.strip()], target_file')
    
    # For response-network parsing (which differs slightly)
    content = content.replace('return json.load(bio)',
                              'return json.load(bio), target_file')
    content = content.replace("return json.load(f)",
                              'return json.load(f), file_path.name')
                              
    # Fix Local path return
    content = content.replace('return json.loads(decrypted_data.decode("utf-8"))',
                              'return json.loads(decrypted_data.decode("utf-8")), file_path.name')

    # Add archive_file method
    archive_code = """
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
"""
    if 'def archive_file' not in content:
        content += archive_code

    with open(filepath, 'w') as f:
        f.write(content)

patch_file("../request-network/api/services/import_storage.py")
patch_file("../response-network/api/services/import_storage.py")
print("Patched ImportStorageService")
