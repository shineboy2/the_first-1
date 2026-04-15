"""
Export request types (with parameters) to Request Network (Synchronous version).
"""
from datetime import datetime
import json
import os
import io
from pathlib import Path
import ftplib
import logging

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, joinedload
from dotenv import load_dotenv

from models.request_type import RequestType
from models.request_type_parameter import RequestTypeParameter

load_dotenv()

logger = logging.getLogger(__name__)


@shared_task
def export_request_types_to_request_network():
    """Export all active request types with parameters to Request Network (Sync)."""
    
    # Build database URL from env
    db_user = os.getenv("RESPONSE_DB_USER", "postgres")
    db_pass = os.getenv("RESPONSE_DB_PASSWORD", "postgres")
    db_host = os.getenv("RESPONSE_DB_HOST", "127.0.0.1")
    db_port = os.getenv("RESPONSE_DB_PORT", "5432")
    db_name = os.getenv("RESPONSE_DB_NAME", "response_network")
    
    database_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get all request types with parameters eager loaded
        result = session.execute(
            select(RequestType)
            .options(joinedload(RequestType.parameters))
            .order_by(RequestType.name)
        )
        request_types = result.unique().scalars().all()
        
        # Prepare export data
        export_data = []
        for rt in request_types:
            export_data.append({
                "id": str(rt.id),
                "name": rt.name,
                "description": rt.description,
                "is_active": rt.is_active,
                "is_public": rt.is_public,
                "version": rt.version,
                "max_items_per_request": rt.max_items_per_request,
                "available_indices": rt.available_indices or [],
                "elasticsearch_query_template": rt.elasticsearch_query_template or {},
                "parameters": [
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "description": p.description,
                        "parameter_type": p.parameter_type,
                        "is_required": p.is_required,
                        "validation_rules": p.validation_rules,
                        "placeholder_key": p.placeholder_key,
                    }
                    for p in rt.parameters
                ],
            })
        
        # Retrieve dynamic export config (reuse settings_export_config or use own)
        from models.settings import Settings as SettingsModel
        config_result = session.execute(
            select(SettingsModel).where(SettingsModel.key == "settings_export_config")
        )
        config_setting = config_result.scalar_one_or_none()
        config = config_setting.value if config_setting else {}
        
        if not config.get("enabled", False):
            logger.info("Request types export is disabled (settings_export_config.enabled=false).")
            return {"status": "skipped", "reason": "disabled"}
        
        filename = "latest.json"
        json_bytes = json.dumps(export_data, indent=2, ensure_ascii=False).encode("utf-8")
        
        storage_type = config.get("storage_type", "local")
        
        if storage_type == "local":
            local_base = Path(config.get("local_path", "/app/exports/settings")).parent
            local_path = local_base / "request_types"
            local_path.mkdir(parents=True, exist_ok=True)
            
            file_path = local_path / filename
            with open(file_path, "wb") as f:
                f.write(json_bytes)
            
            logger.info(f"Exported {len(export_data)} request types to {file_path}")
            return {
                "status": "success",
                "total_count": len(export_data),
                "file": str(file_path),
                "method": "local"
            }
        
        elif storage_type == "ftp":
            host = config.get("ftp_host")
            user = config.get("ftp_user")
            passwd = config.get("ftp_password")
            port = config.get("ftp_port", 21)
            base_remote = config.get("ftp_path", "/uploads/settings")
            remote_path = base_remote.rsplit("/", 1)[0] + "/request_types"
            use_tls = config.get("ftp_use_tls", False)
            
            if not host:
                return {"status": "error", "reason": "ftp_host_missing"}
            
            bio = io.BytesIO(json_bytes)
            
            if use_tls:
                ftp = ftplib.FTP_TLS()
            else:
                ftp = ftplib.FTP()
            
            ftp.connect(host, port)
            ftp.login(user=user, passwd=passwd)
            
            try:
                ftp.cwd(remote_path)
            except ftplib.error_perm:
                try:
                    ftp.mkd(remote_path)
                    ftp.cwd(remote_path)
                except:
                    pass
            
            ftp.storbinary(f"STOR {filename}", bio)
            ftp.quit()
            
            logger.info(f"Exported {len(export_data)} request types to FTP: {remote_path}/{filename}")
            return {
                "status": "success",
                "total_count": len(export_data),
                "method": "ftp",
                "destination": f"ftp://{host}{remote_path}/{filename}"
            }
        
        return {"status": "error", "reason": f"unknown_storage_type_{storage_type}"}
    
    except Exception as e:
        logger.error(f"Request types export failed: {e}")
        return {"status": "error", "reason": str(e)}
    finally:
        session.close()
