from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import RedisDsn, AnyHttpUrl, PostgresDsn
from typing import Optional, Any
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_NAME: str = "Request Network API"
    API_V1_STR: str = "/api/v1"

    # --- Database Settings ---
    REQUEST_DB_USER: str = "requser"
    REQUEST_DB_PASSWORD: str = "reqpassword123"
    REQUEST_DB_HOST: str = "postgres-request-db"
    REQUEST_DB_PORT: int = 5432
    REQUEST_DB_NAME: str = "request_network_db"

    # Secret key for JWT
    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    LOG_LEVEL: str = "INFO"
    DB_ECHO_LOG: bool = False

    # Redis URL (for Celery stats)
    REDIS_URL: RedisDsn = "redis://request-redis:6379/0"

    # Elasticsearch URL for monitoring
    # ELASTICSEARCH_URL: AnyHttpUrl = "http://elasticsearch:9200" # Not used in Request Network
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://request-redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://request-redis:6379/1"
    
    # Import/Export directories
    IMPORT_DIR: str = "/app/imports"
    EXPORT_DIR: str = "/app/exports"
    
    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:3001,http://localhost:3000,http://192.168.214.146:3002,http://192.168.214.146:3000,http://192.168.214.141:3001"

    @property
    def cors_origins_list(self) -> list[str]:
        if isinstance(self.BACKEND_CORS_ORIGINS, list):
            return self.BACKEND_CORS_ORIGINS
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            # Parse comma-separated or JSON list
            if self.BACKEND_CORS_ORIGINS.startswith("["):
                import json
                try:
                    return json.loads(self.BACKEND_CORS_ORIGINS)
                except:
                    pass
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]
        return []

    model_config = SettingsConfigDict(
        env_file=[".env", "/app/.env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.REQUEST_DB_USER}:{self.REQUEST_DB_PASSWORD}@{self.REQUEST_DB_HOST}:{self.REQUEST_DB_PORT}/{self.REQUEST_DB_NAME}"


settings = Settings()