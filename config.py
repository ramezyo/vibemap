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
    
    # API Keys for real-time data
    openweather_api_key: str = ""  # OpenWeatherMap API key
    twitter_bearer_token: str = ""  # Twitter/X API bearer token
    google_places_api_key: str = ""  # Google Places API key
    
    class Config:
        env_file = ".env"
        env_prefix = ""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Convert PostgreSQL URL to use async driver
        if self.database_url and self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if self.database_url and self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)


@lru_cache()
def get_settings() -> Settings:
    return Settings()