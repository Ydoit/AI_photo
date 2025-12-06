import os
import shutil
from uuid import UUID
from fastapi import UploadFile
from PIL import Image
import logging

UPLOAD_DIR = "uploads/uploads"
THUMBNAIL_DIR = "uploads/thumbnails"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

def save_upload_file(upload_file: UploadFile, file_id: UUID) -> str:
    # Get extension
    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{file_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return file_path

def generate_thumbnail(file_path: str, file_id: UUID):
    try:
        # Check if image
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            with Image.open(file_path) as img:
                img.thumbnail((300, 300))
                thumb_path = os.path.join(THUMBNAIL_DIR, f"{file_id}.jpg")
                img.save(thumb_path, "JPEG")
                return thumb_path
    except Exception as e:
        logging.error(f"Error generating thumbnail for {file_path}: {e}")
    return None

def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)

def get_image_dimensions(file_path: str):
    try:
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            with Image.open(file_path) as img:
                return img.width, img.height
    except:
        pass
    return None, None

def delete_file(file_path: str, file_id: UUID):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete thumbnail
        thumb_path = os.path.join(THUMBNAIL_DIR, f"{file_id}.jpg")
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
            
    except Exception as e:
        logging.error(f"Error deleting file {file_path}: {e}")
