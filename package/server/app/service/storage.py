import os
import traceback
import shutil
from uuid import UUID
from typing import Optional
from fastapi import UploadFile
from PIL import Image
from pillow_heif import register_heif_opener
# Register HEIF opener to enable HEIC/HEIF support in Pillow
register_heif_opener()

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config_manager import config_manager
try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None

# Global cache for storage root (User ID -> Root Path)
_STORAGE_ROOT_CACHE = {}

def _get_storage_root(user_id: UUID, db: Session = None) -> str:
    global _STORAGE_ROOT_CACHE

    # Check cache
    if user_id in _STORAGE_ROOT_CACHE:
        return _STORAGE_ROOT_CACHE[user_id]

    # Get from config
    should_close = False
    if db is None:
        from app.db.session import SessionLocal
        db = SessionLocal()
        should_close = True

    try:
        config = config_manager.get_user_config(user_id, db)
        root = config.storage.photo_storage_path
        if not root:
            root = 'uploads'

        # Ensure directories exist
        try:
            os.makedirs(root, exist_ok=True)
            os.makedirs(os.path.join(root, 'uploads'), exist_ok=True)
            os.makedirs(os.path.join(root, 'thumbnails'), exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to create directories for {root}: {e}")

        # Update cache
        _STORAGE_ROOT_CACHE[user_id] = root
        return root
    finally:
        if should_close:
            db.close()

def update_storage_root_cache(user_id: str, new_root: str):
    """Update the global storage root cache for a user and ensure directories exist."""
    global _STORAGE_ROOT_CACHE
    _STORAGE_ROOT_CACHE[user_id] = new_root
    try:
        os.makedirs(new_root, exist_ok=True)
        os.makedirs(os.path.join(new_root, 'uploads'), exist_ok=True)
        os.makedirs(os.path.join(new_root, 'thumbnails'), exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to create directories for {new_root}: {e}")

def _ensure_unique_path(dir_path: str, filename: str) -> str:
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(dir_path, filename)
    idx = 1
    while os.path.exists(candidate):
        candidate = os.path.join(dir_path, f"{base}({idx}){ext}")
        idx += 1
    return candidate

def save_upload_file(upload_file: UploadFile, file_id: UUID, user_id: str) -> str:
    ext = os.path.splitext(upload_file.filename)[1]
    now = datetime.now()
    year = f"{now.year:04d}"
    month = f"{now.month:02d}"
    root = _get_storage_root(user_id)
    base_dir = os.path.join(root, 'uploads', year, month)
    os.makedirs(base_dir, exist_ok=True)
    target_path = _ensure_unique_path(base_dir, upload_file.filename)
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return target_path

def generate_video_thumbnail(file_path: str, file_id: UUID, user_id: str):
    if cv2 is None:
        logging.warning("opencv-python not installed, skipping video thumbnail generation")
        return None
    try:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        return _save_thumbnails(img, file_id, user_id)
    except Exception as e:
        logging.error(f"Error generating video thumbnail for {file_path}: {e}")
    return None

def _save_thumbnails(img: Image.Image, file_id: UUID, user_id: str) -> str:
    if img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')
    compact = str(file_id).replace('-', '')
    p1, p2 = compact[:2], compact[2:4]
    root = _get_storage_root(user_id)
    base = os.path.join(root, 'thumbnails', p1, p2)
    os.makedirs(base, exist_ok=True)
    m_path = os.path.join(base, f"{compact}.jpg")
    s_path = os.path.join(base, f"{compact}-thumb.jpg")

    # Get settings
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        config = config_manager.get_user_config(user_id, db)
    finally:
        db.close()

    t_size = config.image.thumbnail_size
    p_size = config.image.preview_size
    t_qual = config.image.thumbnail_quality
    p_qual = config.image.preview_quality

    m = img.copy()
    m.thumbnail((p_size, p_size))
    m.save(m_path, "JPEG", quality=p_qual)

    s = img.copy()
    s.thumbnail((t_size, t_size))
    s.save(s_path, "JPEG", quality=t_qual)
    return m_path

def get_preview_path(user_id: UUID, file_id: UUID) -> Optional[str]:
    """Get the absolute path to the preview image if it exists."""
    compact = str(file_id).replace('-', '')
    p1, p2 = compact[:2], compact[2:4]
    root = _get_storage_root(user_id)
    m_path = os.path.join(root, 'thumbnails', p1, p2, f"{compact}.jpg")
    if os.path.exists(m_path):
        return m_path
    return None

def generate_thumbnail(user_id: UUID, file_path: str, file_id: UUID, image_obj: Optional[Image.Image] = None):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ('.mp4', '.mov', '.avi', '.mkv', '.webm'):
            return generate_video_thumbnail(file_path, file_id, user_id)
        if ext in ('.png', '.jpg', '.jpeg', '.webp', '.heic'):
            if image_obj:
                return _save_thumbnails(image_obj, file_id, user_id)
            else:
                with Image.open(file_path) as img:
                    return _save_thumbnails(img, file_id, user_id)
    except Exception as e:
        logging.error(f"Error generating thumbnail for {file_path}: {e}\n{traceback.format_exc()}")
    return None

def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)

def get_image_dimensions(file_path: str, image_obj: Optional[Image.Image] = None):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ('.png', '.jpg', '.jpeg', '.webp', '.heic'):
            if image_obj:
                return image_obj.width, image_obj.height, None
            else:
                with Image.open(file_path) as img:
                    return img.width, img.height, None
        elif ext in ('.mp4', '.mov', '.avi', '.mkv', '.webm'):
            if cv2 is None:
                return None, None, None
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return None, None, None
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps else 0
            cap.release()
            return width, height, duration
    except:
        pass
    return None, None, None

def delete_thumbnails(user_id: UUID, file_id: UUID):
    try:
        compact = str(file_id).replace('-', '')
        p1, p2 = compact[:2], compact[2:4]
        root = _get_storage_root(user_id)
        base = os.path.join(root, 'thumbnails', p1, p2)
        m = os.path.join(base, f"{compact}.jpg")
        s = os.path.join(base, f"{compact}-thumb.jpg")
        if os.path.exists(m):
            os.remove(m)
        if os.path.exists(s):
            os.remove(s)
    except Exception as e:
        logging.error(f"Error deleting thumbnails for {user_id}/{file_id}: {e}")
        
def delete_file(user_id: UUID, file_path: str, file_id: UUID):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        delete_thumbnails(user_id, file_id)
    except Exception as e:
        logging.error(f"Error deleting file {user_id}/{file_path}: {e}")
