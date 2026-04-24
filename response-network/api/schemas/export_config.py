"""
Export Configuration Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class ExportConfigUpdate(BaseModel):
    """Configuration for what data gets exported to Request Network"""
    
    request_types_export_enabled: bool = Field(default=True, description="Export Request Types")
    request_types_filter_by_is_active: bool = Field(default=True, description="Only export Request Types with is_active=true")
    
    users_export_enabled: bool = Field(default=True, description="Export Users")
    users_filter_by_is_active: bool = Field(default=True, description="Only export active users")
    users_include_roles: List[str] = Field(default=["admin", "user"], description="Which roles to export")
    
    profile_types_export_enabled: bool = Field(default=True, description="Export ProfileTypes")
    profile_types_filter_by_is_active: bool = Field(default=True, description="Only export active ProfileTypes")
    
    export_interval_seconds: int = Field(default=60, ge=10, le=3600, description="Export interval in seconds")
    
    # Destination configuration
    destination_type: Optional[str] = Field(None, description="Destination type: local or ftp")
    local_path: Optional[str] = Field(None, description="Local file system path")
    ftp_host: Optional[str] = Field(None, description="FTP server hostname")
    ftp_port: Optional[int] = Field(None, description="FTP server port")
    ftp_username: Optional[str] = Field(None, description="FTP username")
    ftp_password: Optional[str] = Field(None, description="FTP password")
    ftp_path: Optional[str] = Field(None, description="FTP remote path")
    ftp_use_tls: Optional[bool] = Field(None, description="Use TLS/SSL for FTP")


class ExportConfigResponse(BaseModel):
    """Response with current export configuration"""
    
    request_types_export_enabled: bool
    request_types_filter_by_is_active: bool
    
    users_export_enabled: bool
    users_filter_by_is_active: bool
    users_include_roles: List[str]
    
    profile_types_export_enabled: bool
    profile_types_filter_by_is_active: bool
    
    export_interval_seconds: int
    message: str = ""
    
    # Destination configuration
    destination_type: str = Field(description="Destination type: local or ftp")
    local_path: Optional[str] = Field(None, description="Local file system path")
    ftp_host: Optional[str] = Field(None, description="FTP server hostname")
    ftp_port: Optional[int] = Field(None, description="FTP server port")
    ftp_username: Optional[str] = Field(None, description="FTP username (masked)")
    ftp_password: Optional[str] = Field(None, description="FTP password (masked)")
    ftp_path: Optional[str] = Field(None, description="FTP remote path")
    ftp_use_tls: Optional[bool] = Field(None, description="Use TLS/SSL for FTP")


class ExportStatusResponse(BaseModel):
    """Status of exports"""
    
    settings: dict = Field(description="Settings export status")
    users: dict = Field(description="Users export status")
    profile_types: dict = Field(description="ProfileTypes export status")
