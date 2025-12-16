import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "TrailSnap AI Service"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = ""
    PORT: int = 8001

    # AI Models Configuration
    INSIGHTFACE_MODEL_PATH: str = os.getenv("INSIGHTFACE_MODEL_PATH", os.path.expanduser("~/.insightface/models"))

    class Config:
        env_file = ".env"

settings = Settings()
