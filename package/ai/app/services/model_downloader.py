import os
import logging
import shutil
import threading
from enum import Enum
from typing import Callable, Dict, Any, Optional

from app.config import settings

class ModelStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    READY = "ready"
    FAILED = "failed"

class ModelDownloader:
    def __init__(self):
        self.models: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.base_dir = settings.MODEL_PATH
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def register_model(self, key: str, check_fn: Callable[[], bool], download_fn: Callable[[], str], cleanup_dir: Optional[str] = None):
        """
        Register a model for management.
        :param key: Unique identifier for the model
        :param check_fn: Function that returns True if model exists and is valid
        :param download_fn: Function that performs the download and returns the path
        :param cleanup_dir: Directory to clean up if download fails
        """
        with self.lock:
            self.models[key] = {
                "check_fn": check_fn,
                "download_fn": download_fn,
                "cleanup_dir": cleanup_dir,
                "status": ModelStatus.PENDING,
                "error": None
            }

    def _download_worker(self, key: str):
        model_info = self.models[key]
        cleanup_dir = model_info.get("cleanup_dir")
        
        try:
            # Check if already exists
            if model_info["check_fn"]():
                logging.info(f"Model '{key}' already exists.")
                with self.lock:
                    model_info["status"] = ModelStatus.READY
                return

            logging.info(f"Starting download for model '{key}'...")
            with self.lock:
                model_info["status"] = ModelStatus.DOWNLOADING

            # Execute download
            path = model_info["download_fn"]()
            
            logging.info(f"Model '{key}' downloaded successfully at {path}.")
            with self.lock:
                model_info["status"] = ModelStatus.READY

        except Exception as e:
            logging.error(f"Failed to download model '{key}': {e}")
            
            # Cleanup logic
            if cleanup_dir and os.path.exists(cleanup_dir):
                try:
                    logging.info(f"Cleaning up directory: {cleanup_dir}")
                    shutil.rmtree(cleanup_dir, ignore_errors=True)
                except Exception as cleanup_error:
                    logging.error(f"Failed to cleanup directory {cleanup_dir}: {cleanup_error}")

            with self.lock:
                model_info["status"] = ModelStatus.FAILED
                model_info["error"] = str(e)

    def start_downloads(self):
        """Start all registered model downloads in separate threads."""
        for key in self.models:
            t = threading.Thread(target=self._download_worker, args=(key,), daemon=True)
            t.start()

    def get_status(self, key: str) -> ModelStatus:
        with self.lock:
            return self.models.get(key, {}).get("status", ModelStatus.FAILED)

    def is_ready(self, key: str) -> bool:
        return self.get_status(key) == ModelStatus.READY
    
    def wait_for_model(self, key: str, timeout: int = 60) -> bool:
        """Wait for a model to become ready."""
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_ready(key):
                return True
            time.sleep(1)
        return False

    def reset_status(self, key: str):
        """Reset the status of a model to PENDING."""
        with self.lock:
            if key in self.models:
                self.models[key]["status"] = ModelStatus.PENDING
                self.models[key]["error"] = None

    def trigger_download(self, key: str):
        """Trigger download for a specific model."""
        t = threading.Thread(target=self._download_worker, args=(key,), daemon=True)
        t.start()

model_downloader = ModelDownloader()
