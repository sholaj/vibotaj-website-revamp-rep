"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    app_name: str = "TraceHub"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Database
    database_url: str = "postgresql://tracehub:tracehub@localhost:5432/tracehub"

    # JWT Authentication (v1)
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # PropelAuth (v2) — empty disables PropelAuth
    propelauth_auth_url: str = ""
    propelauth_api_key: str = ""

    # Demo User (POC only - move to database in production)
    enable_demo_credentials: bool = False  # Set to True only in demo environments
    demo_username: str = "demo"
    demo_password: str = ""  # Set via DEMO_PASSWORD env var
    demo_email: str = "demo@vibotaj.com"
    demo_full_name: str = "Demo User"

    # Container Tracking API (JSONCargo)
    jsoncargo_api_key: str = ""
    jsoncargo_api_url: str = "https://api.jsoncargo.com/api/v1"

    # AI Document Classification (Anthropic Claude)
    anthropic_api_key: str = ""

    # Webhook Security
    webhook_secret: str = ""  # HMAC secret for webhook signature verification

    # File Storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50
    storage_backend: str = "local"  # "local" or "supabase"

    # Supabase Storage (PRD-005) — empty disables Supabase storage
    supabase_url: str = ""
    supabase_service_key: str = ""  # Service role key (bypasses RLS for server-side ops)

    # OCR Settings
    tesseract_cmd: str = ""  # Path to tesseract executable (leave empty to use system PATH)
    ocr_enabled: bool = True  # Enable/disable OCR fallback for scanned PDFs
    ocr_dpi: int = 300  # DPI for PDF to image conversion
    ocr_timeout: int = 30  # Timeout per page in seconds
    ocr_language: str = "eng"  # Tesseract language code

    # Monitoring
    sentry_dsn: str = ""  # Sentry DSN — empty disables Sentry

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"]

    # Frontend URL (for invitation links)
    frontend_url: str = "https://tracehub.vibotaj.com"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance for convenience
settings = get_settings()
