import json
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AISettings(BaseModel):
    ai_api_url: str = Field(default=os.getenv("AI_API_URL", "http://localhost:8001"), description="AI Service API URL")
    face_recognition_threshold: float = Field(default=0.6, description="Face recognition confidence threshold")
    face_recognition_min_photos: int = Field(default=5, description="Minimum photos required for a valid face cluster")
    # OCR settings can be added here later

class TaskSettings(BaseModel):
    max_concurrent_tasks: int = Field(default=3, description="Maximum number of concurrent tasks")

class StorageSettings(BaseModel):
    photo_storage_path: str = Field(default="./data/uploads", description="Main photo storage root path")
    external_directories: List[str] = Field(default=[], description="List of external gallery directories")

class ImageSettings(BaseModel):
    thumbnail_quality: int = Field(default=80, description="Thumbnail quality (1-100)")
    preview_quality: int = Field(default=85, description="Preview image quality (1-100)")
    thumbnail_size: int = Field(default=250, description="Thumbnail long edge size")
    preview_size: int = Field(default=1440, description="Preview long edge size")
    # Add other image settings here

class AppSettings(BaseModel):
    version: str = "2.0"
    ai: AISettings = Field(default_factory=AISettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    image: ImageSettings = Field(default_factory=ImageSettings)
    task: TaskSettings = Field(default_factory=TaskSettings)
    
    class Config:
        arbitrary_types_allowed = True

class ConfigManager:
    _instance = None
    _config_path = "./data/config.json"
    _last_mtime = 0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        if not os.path.exists(self._config_path):
            self.config = AppSettings()
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
                        
                    self.config = new_config
                    self._save_config()
                else:
                    # Deep merge or direct load
                    # Since we have nested models, simple **data might fail if structure changed drastically
                    # But Pydantic handles nested dicts well if structure matches
                    self.config = AppSettings(**data)
                    
            except Exception as e:
                print(f"Error loading config: {e}")
                self.config = AppSettings()

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
                f.write(self.config.model_dump_json(indent=4, ensure_ascii=False))
            
            # Update mtime to prevent immediate reload
            if os.path.exists(self._config_path):
                self._last_mtime = os.path.getmtime(self._config_path)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_all(self) -> Dict[str, Any]:
        return self.config.model_dump()

    def update_all(self, new_config: Dict[str, Any]):
        # Update fields in existing config object
        # For nested Pydantic models, we need to be careful. 
        # config.dict() returns a dict, but we want to update the actual object or recreate it.
        # Simplest way is to dump current, merge, and recreate.
        
        current_data = self.config.model_dump()
        
        # Deep merge helper or just simple update?
        # If new_config has partial nested data (e.g. only ai updated), we need deep merge.
        # But usually the frontend sends the whole object or we can assume it does.
        # Let's assume frontend sends matching structure.
        
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = deep_update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d

        updated_data = deep_update(current_data, new_config)
        self.config = AppSettings(**updated_data)
        self._save_config()

# Global instance
config_manager = ConfigManager()
