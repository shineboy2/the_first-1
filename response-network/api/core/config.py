from pydantic import RedisDsn, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Any, List
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_NAME: str = "Response Network Monitoring API"
    API_V1_STR: str = "/api/v1"

    # --- Security Settings ---
    SECRET_KEY: str = "a_very_secret_key_for_response_network_admin"  # Change this in production!
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # --- Database Settings ---
    RESPONSE_DB_USER: str = "postgres"
    RESPONSE_DB_PASSWORD: str = ""
    RESPONSE_DB_HOST: str = "localhost"
    RESPONSE_DB_PORT: int = 5432
    RESPONSE_DB_NAME: str = "response_network"

    # Secret key for API access
    MONITORING_API_KEY: str = "super-secret-monitoring-key"
    LOG_LEVEL: str = "INFO"
    
    # Development mode flag
    DEV_MODE: bool = True

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Redis URL (for Celery stats)
    REDIS_URL: RedisDsn = "redis://redis-response:6379/0"
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://redis-response:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis-response:6379/1"

    # Elasticsearch URL for monitoring and query execution
    ELASTICSEARCH_URL: AnyHttpUrl = "http://192.168.214.139:9200"
    
    # Import/export directories for file exchange with request network
    IMPORT_DIR: str = "/app/imports"
    EXPORT_DIR: str = "./exports"
    
    # Export destination configuration
    EXPORT_DESTINATION_TYPE: str = "local"  # local or ftp
    EXPORT_FTP_HOST: str = ""
    EXPORT_FTP_PORT: int = 21
    EXPORT_FTP_USERNAME: str = ""
    EXPORT_FTP_PASSWORD: str = ""
    EXPORT_FTP_PATH: str = "/exports"
    EXPORT_FTP_USE_TLS: bool = False

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.RESPONSE_DB_USER}:{self.RESPONSE_DB_PASSWORD}@{self.RESPONSE_DB_HOST}:{self.RESPONSE_DB_PORT}/{self.RESPONSE_DB_NAME}"


    model_config = SettingsConfigDict(
        env_file=[".env", "/app/.env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()