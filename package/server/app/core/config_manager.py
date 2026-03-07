import json
import os
from typing import Any, Dict, List, Optional
from contextvars import ContextVar
from pydantic import BaseModel, Field

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
    _config_path = "./data/config.json"
    _last_mtime = 0
    _user_config_ctx = ContextVar("user_config", default=None)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    @property
    def config(self) -> AppSettings:
        """Get the current configuration (user-specific if context is set, otherwise system default)."""
        user_config = self._user_config_ctx.get()
        return user_config if user_config else self._system_config

    @config.setter
    def config(self, value: AppSettings):
        """Set the system configuration (only used during initialization/loading)."""
        self._system_config = value

    def set_user_context(self, user_settings: Dict[str, Any]):
        """Set the user context for the current request/task."""
        merged_config = self.merge_user_settings(user_settings)
        self._user_config_ctx.set(merged_config)

    def clear_user_context(self):
        """Clear the user context."""
        self._user_config_ctx.set(None)

    def _load_config(self):
        if not os.path.exists(self._config_path):
            self._system_config = AppSettings()
            self._save_config()
            self._last_mtime = os.path.getmtime(self._config_path) if os.path.exists(self._config_path) else 0
        else:
            try:
                current_mtime = os.path.getmtime(self._config_path)
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._last_mtime = current_mtime
                
                # Migration Logic
                if data.get("version") == "1.0" or "storage_root" in data:
                    print("Migrating config from version 1.0 to 2.0...")
                    new_config = AppSettings()
                    
                    # Migrate Storage
                    if "storage_root" in data:
                        new_config.storage.photo_storage_path = data["storage_root"]
                    if "external_directories" in data:
                        new_config.storage.external_directories = data["external_directories"]
                    
                    # Migrate AI
                    if "ai_api_url" in data:
                        new_config.ai.ai_api_url = data["ai_api_url"]
                    if "face_recognition_threshold" in data:
                        new_config.ai.face_recognition_threshold = data["face_recognition_threshold"]
                    if "face_recognition_min_photos" in data:
                        new_config.ai.face_recognition_min_photos = data["face_recognition_min_photos"]
                        
                    self._system_config = new_config
                    self._save_config()
                else:
                    # Deep merge or direct load
                    # Since we have nested models, simple **data might fail if structure changed drastically
                    # But Pydantic handles nested dicts well if structure matches
                    
                    # Migration for map api_key -> api_keys
                    if "map" in data and isinstance(data["map"], dict):
                        map_data = data["map"]
                        if "api_key" in map_data:
                            if map_data["api_key"] and "api_keys" not in map_data:
                                map_data["api_keys"] = [map_data["api_key"]]
                            # Remove old key to avoid validation error if extra fields are forbidden
                            # or just cleanup
                            del map_data["api_key"]

                    self._system_config = AppSettings(**data)
                    
            except Exception as e:
                print(f"Error loading config: {e}")
                self._system_config = AppSettings()

    def save(self):
        self._save_config()

    def reload(self):
        """Reload config from disk if changed"""
        if not os.path.exists(self._config_path):
            return

        try:
            mtime = os.path.getmtime(self._config_path)
            if mtime > self._last_mtime:
                # print(f"Config changed on disk, reloading... (old: {self._last_mtime}, new: {mtime})")
                self._load_config()
        except Exception as e:
            print(f"Error checking config file: {e}")

    def _save_config(self):
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                # Always save system config to disk
                f.write(self._system_config.model_dump_json(indent=4, ensure_ascii=False))
            
            # Update mtime to prevent immediate reload
            if os.path.exists(self._config_path):
                self._last_mtime = os.path.getmtime(self._config_path)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_all(self) -> Dict[str, Any]:
        # Return current context config (user or system)
        return self.config.model_dump()

    def update_all(self, new_config: Dict[str, Any]):
        # This method updates the *current context* config.
        # But wait, if we are in user context, we shouldn't update self._system_config unless explicitly requested?
        # The prompt says: "Modify config... read from DB... modify... save to DB".
        # So this method might be less relevant if we use DB persistence directly in API.
        # But for compatibility, let's keep it updating the SYSTEM config for now, 
        # or make it raise an error if in user context?
        # Actually, let's just update the system config here (legacy behavior), 
        # but the API should handle DB updates.
        
        current_data = self._system_config.model_dump()
        
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = deep_update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d

        updated_data = deep_update(current_data, new_config)
        self._system_config = AppSettings(**updated_data)
        self._save_config()

    def merge_user_settings(self, user_settings: Dict[str, Any]) -> AppSettings:
        """
        Merge system config with user settings.
        Returns a new AppSettings object with user overrides.
        """
        if not user_settings:
            return self._system_config

        # Start with system config as base
        current_data = self._system_config.model_dump()

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

# Global instance
config_manager = ConfigManager()
VERSION = "0.2.4"