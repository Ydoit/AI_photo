import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "TrailSnap AI Service"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = ""
    PORT: int = 8001

    # AI Models Configuration
    MODEL_PATH: str = os.getenv("MODEL_PATH", os.path.expanduser("data/models"))
    class Config:
        env_file = ".env"

settings = Settings()
