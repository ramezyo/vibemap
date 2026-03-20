from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Vibemap application settings."""
    
    # Application
    app_name: str = "Vibemap"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database - SQLite for demo/testing, PostgreSQL for production
    database_url: str = "sqlite+aiosqlite:///./vibemap.db"
    sync_database_url: str = "sqlite:///./vibemap.db"
    
    # Redis (optional for demo)
    redis_url: str = ""
    
    # Genesis Anchor - Wynwood, Miami
    genesis_lat: float = 25.7997
    genesis_lon: float = -80.1986
    genesis_name: str = "Genesis Anchor - Wynwood"
    
    # Vibe calculation
    vibe_decay_hours: float = 24.0  # How fast vibe energy decays
    vibe_radius_meters: float = 500.0  # Radius for vibe aggregation
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
