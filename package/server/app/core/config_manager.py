import json
import os
import time
from collections import OrderedDict
from uuid import UUID
from typing import Any, Dict, List, Optional, Tuple
from contextvars import ContextVar
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

class LLMSettings(BaseModel):
    base_url: str = Field(default="", description="LLM API base URL")
    model_name: str = Field(default="", description="LLM model name")
    api_key: str = Field(default="", description="LLM API key")

class AISettings(BaseModel):
    llm_settings: LLMSettings = Field(default_factory=LLMSettings)
    llm_vl_settings: LLMSettings = Field(default_factory=LLMSettings)
    ai_api_url: str = Field(default=os.getenv("AI_API_URL", "http://localhost:8001"), description="AI Service API URL")
    face_recognition_threshold: float = Field(default=0.7, description="Face recognition confidence threshold")
    face_cluster_threshold: float = Field(default=0.4, description="Face cluster distance threshold")
    face_recognition_min_photos: int = Field(default=5, description="Minimum photos required for a valid face cluster")
    classification_tag_threshold: float = Field(default=0.25, description="Classification tag confidence threshold")
    # OCR settings can be added here later

class TaskSettings(BaseModel):
    max_concurrent_tasks: int = Field(default=10, description="Maximum number of concurrent tasks")

class StorageSettings(BaseModel):
    photo_storage_path: str = Field(default="./data/uploads", description="Main photo storage root path")
    external_directories: List[str] = Field(default=[], description="List of external gallery directories")

class ImageSettings(BaseModel):
    thumbnail_quality: int = Field(default=80, description="Thumbnail quality (1-100)")
    preview_quality: int = Field(default=85, description="Preview image quality (1-100)")
    thumbnail_size: int = Field(default=250, description="Thumbnail long edge size")
    preview_size: int = Field(default=1440, description="Preview long edge size")
    # Add other image settings here

class FilterSettings(BaseModel):
    enable: bool = Field(default=False, description="Enable file filtering")
    min_size_kb: int = Field(default=0, description="Minimum file size in KB")
    min_width: int = Field(default=0, description="Minimum image width")
    min_height: int = Field(default=0, description="Minimum image height")
    filename_patterns: List[str] = Field(default=[], description="List of regex patterns to filter out files")

class MapSettings(BaseModel):
    provider: str = Field(default="tianditu", description="Map provider (tianditu, amap, baidu)")
    api_keys: List[str] = Field(default=[], description="Map API Key")

class SecuritySettings(BaseModel):
    secret_key: str = Field(default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7", description="Secret key for JWT")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=60*24*3, description="Access token expiration in minutes")

class AppSettings(BaseModel):
    version: str = "0.2.4"
    ai: AISettings = Field(default_factory=AISettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    image: ImageSettings = Field(default_factory=ImageSettings)
    filter: FilterSettings = Field(default_factory=FilterSettings)
    task: TaskSettings = Field(default_factory=TaskSettings)
    map: MapSettings = Field(default_factory=MapSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    class Config:
        arbitrary_types_allowed = True

class ConfigManager:
    _instance = None
    _user_config_ctx = ContextVar("user_config", default=None)
    
    # LRU Cache for user configurations
    _user_cache: OrderedDict = OrderedDict()
    _cache_size = 100
    _cache_ttl = 5.0  # seconds
    config = AppSettings()
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def get_user_config(self, user_id: UUID, db: Session) -> AppSettings:
        """
        Get user configuration with LRU caching.
        Checks cache first, then DB.
        """
        # Check cache
        if user_id in self._user_cache:
            config, ts = self._user_cache[user_id]
            # Check TTL to ensure freshness across processes
            if time.time() - ts < self._cache_ttl:
                self._user_cache.move_to_end(user_id)
                return config

        # Load from DB
        from app.db.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        
        if user and user.settings:
             config = self.merge_user_settings(user.settings)
        else:
             config = AppSettings()
        
        # Update cache
        self._user_cache[user_id] = (config, time.time())
        self._user_cache.move_to_end(user_id)
        
        # Maintain cache size
        if len(self._user_cache) > self._cache_size:
            self._user_cache.popitem(last=False)
            
        return config

    def update_user_config(self, user_id: UUID, settings: dict, db: Session) -> AppSettings:
        """
        Update user configuration in DB and cache.
        """
        from app.db.models.user import User
        from sqlalchemy.orm.attributes import flag_modified

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
             raise ValueError(f"User {user_id} not found")

        # Merge existing settings with new settings
        current_settings = dict(user.settings) if user.settings else {}

        # Deep merge helper
        def deep_merge(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
            return target

        updated_settings = deep_merge(current_settings, settings)
        user.settings = updated_settings
        flag_modified(user, "settings")
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Update cache immediately
        new_config = self.merge_user_settings(updated_settings)
        self._user_cache[user_id] = (new_config, time.time())
        self._user_cache.move_to_end(user_id)
        
        return new_config

    def merge_user_settings(self, user_settings: Dict[str, Any]) -> AppSettings:
        """
        Merge default config with user settings.
        Returns a new AppSettings object with user overrides.
        """
        if not user_settings:
            return AppSettings()

        # Start with default config as base
        current_data = AppSettings().model_dump()

        # Deep merge user settings
        def deep_merge(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
            return target

        merged_data = deep_merge(current_data, user_settings)
        
        return AppSettings(**merged_data)

    def get_default_config(self) -> Dict[str, Any]:
        """Return the default config as a dict."""
        return AppSettings().model_dump()

os.makedirs('./data', exist_ok=True)
os.makedirs('./data/uploads', exist_ok=True)
# Global instance
config_manager = ConfigManager()
VERSION = "0.2.4"