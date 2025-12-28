import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "TrailSnap AI Service"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = ""
    PORT: int = 8001

    # AI Models Configuration
    MODEL_PATH: str = os.getenv("MODEL_PATH", os.path.expanduser("data/models"))

    # Memory Management
    IDLE_TIMEOUT: int = 600  # Default 1 hour in seconds
    CHECK_INTERVAL: int = 60  # Check every minute

    class Config:
        env_file = ".env"

settings = Settings()
