"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "TraceHub"
    debug: bool = False

    # Database
    database_url: str = "postgresql://tracehub:tracehub@localhost:5432/tracehub"

    # JWT Authentication
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Container Tracking API (JSONCargo - primary)
    jsoncargo_api_key: str = ""
    jsoncargo_api_url: str = "https://api.jsoncargo.com/api/v1"

    # Vizion API (legacy/backup)
    vizion_api_key: str = ""
    vizion_api_url: str = "https://api.vizionapi.com/v2"

    # File Storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
