from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "seabridge"

    ANTHROPIC_API_KEY: str = ""
    MAPBOX_TOKEN: str = ""

    # Guard: when False all data providers return stubs; no external HTTP calls
    ENABLE_LIVE_DATA: bool = False

    NASA_EARTHDATA_TOKEN: str = ""
    IUCN_API_KEY: str = ""
    PHYSRISK_ZARR_STORE: str = ""

    LOG_LEVEL: str = "INFO"


settings = Settings()
