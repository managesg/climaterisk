"""Configuration via environment variables. No secrets hardcoded."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "SeaBridge AI Sustainability Toolkit"
    app_version: str = "0.1.0"
    debug: bool = False

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "climaterisk"

    # LLM
    anthropic_api_key: Optional[str] = None
    llm_model: str = "claude-sonnet-4-6"

    # Mapbox
    mapbox_token: Optional[str] = None

    # Data providers (all off by default — open-access only in MVP)
    enable_paid_providers: bool = False
    enable_fema_api: bool = False
    enable_wri_aqueduct: bool = False
    enable_iucn_api: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Logging
    log_level: str = "INFO"


settings = Settings()
