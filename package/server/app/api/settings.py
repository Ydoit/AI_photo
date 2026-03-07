from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, or_
import os
import tempfile
import json
import re
import logging
from app.dependencies import get_db
from app.api.deps import get_current_user
from app.db.models.user import User
from app.core.config_manager import config_manager
from app.db.models.photo import Photo
from app.db.models.task import TaskType
from app.service.storage import delete_thumbnails, update_storage_root_cache, _get_storage_root
from app.service.indexer import rebuild_index as service_rebuild_index, status as index_status
from app.db.models.index_log import IndexLog
from app.service.task_manager import TaskManager
from app.db.session import SessionLocal
# Import reverse_geocoder from the local package
# Assuming package/server is in sys.path or accessible
try:
    from reverse_geocoder import download_country_data
except ImportError:
    import sys
    # Add package/server to path if not present (heuristic)
    # Go up 2 levels: api -> app -> server
    server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    if server_path not in sys.path:
        sys.path.insert(0, server_path)
    from reverse_geocoder import download_country_data

router = APIRouter()

RG_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'rg_data')
COUNTRIES_JSON_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'rg_data', 'countries.json')

def get_storage_root() -> str:
    return _get_storage_root()

class PathValidator:
    @staticmethod
    def validate(path: str) -> str:
        path = path.strip()
        if not path:
            raise HTTPException(status_code=400, detail='Invalid path')
        
        # Prevent directory traversal
        if '..' in path:
             raise HTTPException(status_code=400, detail='Invalid path: traversal detected')
             
        if not os.path.exists(path):
             raise HTTPException(status_code=400, detail='Path does not exist')
             
        if not os.path.isdir(path):
            raise HTTPException(status_code=400, detail='Path is not a directory')
            
        return os.path.abspath(path)

@router.get('/directories')
def get_directories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: str = None
):
    target_user = current_user
    if user_id:
        if not current_user.is_superuser:
            # Non-admin cannot see other's directories
            # But maybe we should just ignore user_id? 
            # Spec says: "If provided and current_user is superuser, return that user's directories. Otherwise return current_user's."
            # So we just ignore it if not superuser.
            pass
        else:
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                raise HTTPException(status_code=404, detail="User not found")

    primary = get_storage_root()
    external = target_user.settings.get('storage',{}).get('external_directories', []) if target_user.settings else []
    return {'primary': primary, 'external': external}

@router.post('/directories')
def add_directory(
    payload: dict, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    user_id = payload.get('user_id')
    target_user = current_user
    if user_id:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

    raw_path = payload.get('path')
    if not raw_path or not isinstance(raw_path, str):
         raise HTTPException(status_code=400, detail='invalid path')

    path = PathValidator.validate(raw_path)
    
    # Update target user settings
    if not target_user.settings:
        target_user.settings = {}
        
    settings = dict(target_user.settings)
    external = settings.get('external_directories', [])
    
    if path in external:
        return {'primary': get_storage_root(), 'external': external}
    
    external.append(path)
    settings['external_directories'] = external
    target_user.settings = settings
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(target_user, "settings")
    
    db.add(target_user)
    db.commit()
    db.refresh(target_user)

    # Trigger scan to update index
    TaskManager.get_instance().add_task(db, TaskType.SCAN_FOLDER, {'scan_roots': external, 'user_id': str(target_user.id)})
    config_manager.set_user_context(settings)
    return {'primary': get_storage_root(), 'external': external}

@router.delete('/directories')
def remove_directory(
    payload: dict, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    path = payload.get('path')
    if not path:
        raise HTTPException(status_code=400, detail='path required')

    user_id = payload.get('user_id')
    target_user = current_user
    if user_id:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
    
    if not target_user.settings:
        return {'primary': get_storage_root(), 'external': []}

    settings = dict(target_user.settings)
    external = settings.get('external_directories', [])
    
    if path in external:
        external.remove(path)
        settings['external_directories'] = external
        target_user.settings = settings
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(target_user, "settings")
        db.add(target_user)
        
        # Cleanup photos belonging to this directory and user
        norm_path = os.path.normpath(path)
        photos = db.query(Photo).filter(Photo.owner_id == target_user.id).all()
        
        for p in photos:
            if os.path.normpath(p.file_path).startswith(norm_path):
                delete_thumbnails(p.id)
                db.delete(p)
                db.add(IndexLog(action='deleted', file_path=p.file_path, photo_id=p.id, owner_id=target_user.id))
        
        db.commit()
        db.refresh(target_user)

    return {'primary': get_storage_root(), 'external': external}

@router.get('/storage-root')
def read_storage_root(db: Session = Depends(get_db)):
    return {'storage_root': get_storage_root()}

@router.put('/storage-root')
def update_storage_root(payload: dict, db: Session = Depends(get_db)):
    path = payload.get('storage_root')
    if not path or not isinstance(path, str):
        raise HTTPException(status_code=400, detail='invalid path')
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail='not a directory')
    try:
        fd, tmp = tempfile.mkstemp(prefix='ts_test_', dir=path)
        os.close(fd)
        os.remove(tmp)
    except Exception:
        raise HTTPException(status_code=400, detail='rw check failed')
    config_manager.config.storage.photo_storage_path = path
    config_manager.save()
    # Update global cache
    update_storage_root_cache(path)
    return {'storage_root': path}

@router.get('/')
def get_settings(current_user: User = Depends(get_current_user)):
    user_settings = current_user.settings if current_user.settings else {}
    return config_manager.merge_user_settings(user_settings).model_dump()

@router.put('/')
def update_settings(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure user settings dict exists
    if not current_user.settings:
        current_user.settings = {}
    
    # We need to work with a copy to ensure SQLAlchemy detects changes
    user_settings = dict(current_user.settings)

    # Helper to deep merge payload into user_settings
    def deep_merge(target, source):
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                deep_merge(target[key], value)
            else:
                target[key] = value
        return target

    # Merge payload into user settings
    deep_merge(user_settings, payload)
    
    # Save back to user
    current_user.settings = user_settings
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(current_user, "settings")
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    # Update context for the current request (if we were using ContextVar dependency)
    # But since this is the end of request, it matters less, unless we trigger tasks.
    # If we trigger tasks here, we should pass the new config.
    
    # Check if storage root changed to update cache
    # We need to resolve the full config to see the effective storage root
    full_config = config_manager.merge_user_settings(user_settings)
    root = full_config.storage.photo_storage_path
    if root:
        update_storage_root_cache(root)
    config_manager.set_user_context(user_settings)
    return {"status": "success", "config": full_config.model_dump()}

def apply_filter_task_bg(user_id: str = None):
    db = SessionLocal()
    try:
        logging.info(f"Starting filter application task for user {user_id}...")
        
        user_settings = {}
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.settings:
                user_settings = user.settings
        
        merged_config = config_manager.merge_user_settings(user_settings)
        filter_config = merged_config.filter

        if not filter_config.enable:
            logging.info("Filter disabled, skipping.")
            return

        deleted_count = 0
        
        # 1. SQL-based filtering (Size and Dimensions)
        filters = []
        if filter_config.min_size_kb > 0:
            min_bytes = filter_config.min_size_kb * 1024
            filters.append(Photo.size < min_bytes)
            
        if filter_config.min_width > 0:
            filters.append(Photo.width < filter_config.min_width)
            
        if filter_config.min_height > 0:
            filters.append(Photo.height < filter_config.min_height)
            
        if filters:
             query = db.query(Photo)
             if user_id:
                 query = query.filter(Photo.owner_id == user_id)
             
             photos_to_delete = query.filter(or_(*filters)).all()
             for p in photos_to_delete:
                 delete_thumbnails(p.id)
                 db.delete(p)
                 db.add(IndexLog(action='deleted', file_path=p.file_path, photo_id=p.id, owner_id=p.owner_id))
                 deleted_count += 1
             db.commit()
             
        # 2. Regex-based filtering (Filename)
        patterns = filter_config.filename_patterns
        if patterns:
            # Compile all valid patterns
            compiled_patterns = []
            for pattern in patterns:
                try:
                    if pattern:
                        compiled_patterns.append(re.compile(pattern))
                except re.error:
                    logging.error(f"Invalid regex pattern: {pattern}")
            
            if compiled_patterns:
                # Fetch all remaining photos to check filename
                query = db.query(Photo.id, Photo.file_path)
                if user_id:
                    query = query.filter(Photo.owner_id == user_id)
                
                all_photos = query.all()
                
                for pid, path in all_photos:
                    basename = os.path.basename(path)
                    matched = False
                    for cp in compiled_patterns:
                        if cp.search(basename):
                            matched = True
                            break
                    
                    if matched:
                        # Re-fetch to delete (ensure it still exists)
                        p = db.query(Photo).get(pid)
                        if p:
                            delete_thumbnails(p.id)
                            db.delete(p)
                            db.add(IndexLog(action='deleted', file_path=p.file_path, photo_id=p.id, owner_id=p.owner_id))
                            deleted_count += 1
                db.commit()

        logging.info(f"Filter applied. Deleted {deleted_count} files.")
        
    except Exception as e:
        logging.error(f"Error applying filter: {e}")
        db.rollback()
    finally:
        db.close()

@router.post('/filter/apply')
def apply_filter(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    background_tasks.add_task(apply_filter_task_bg, str(current_user.id))
    return {"status": "started", "message": "Filter application started in background"}

@router.get('/export')
def export_settings():
    return config_manager.get_all()

@router.post('/import')
def import_settings(payload: dict):
    config_manager.update_all(payload)
    # Update cache if storage_root changed
    root = config_manager.config.storage.photo_storage_path
    if root:
        update_storage_root_cache(root)
    return {"status": "success", "config": config_manager.get_all()}

@router.get('/map/countries')
def get_map_countries():
    if not os.path.exists(COUNTRIES_JSON_FILE):
        return []
    with open(COUNTRIES_JSON_FILE, 'r') as f:
        countries = json.load(f)
    return countries

@router.get('/map/downloaded')
def get_downloaded_countries():
    if not os.path.exists(RG_DATA_DIR):
        return []
    files = os.listdir(RG_DATA_DIR)
    # Filter for .csv files and map to country codes if possible
    downloaded = []
    for f in files:
        if f.endswith('.csv'):
            code = f[:-4]
            # Try to find name
            name = code
            for c in get_map_countries():
                if c['code'] == code:
                    name = c['name']
                    break
            downloaded.append({"code": code, "name": name, "filename": f})
    return downloaded

@router.post('/map/download')
def download_map_data(payload: dict, background_tasks: BackgroundTasks):
    code = payload.get('code')
    if not code:
         raise HTTPException(status_code=400, detail='Country code required')

    # We can run this in background
    background_tasks.add_task(download_country_data, code, RG_DATA_DIR)
    return {"status": "downloading", "code": code}

@router.post('/map/upload')
async def upload_map_data(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail='Only CSV files are allowed')

    # Validate headers
    content = await file.read()
    # Need to read first line
    try:
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
         raise HTTPException(status_code=400, detail='Invalid encoding')

    lines = text_content.splitlines()
    if not lines:
        raise HTTPException(status_code=400, detail='Empty file')

    header = lines[0].strip().split(',')
    required = ['longitude','latitude','country','admin_1','admin_2','admin_3','admin_4']

    # Check if all required columns are present.
    if not all(col in header for col in required):
         raise HTTPException(status_code=400, detail=f'Missing required columns: {required}')

    # Save file
    if not os.path.exists(RG_DATA_DIR):
        os.makedirs(RG_DATA_DIR)

    file_path = os.path.join(RG_DATA_DIR, file.filename)
    with open(file_path, 'wb') as f:
        f.write(content)

    return {"status": "success", "filename": file.filename}

@router.get('/map/files/{filename}')
def download_map_file(filename: str):
    if not os.path.exists(RG_DATA_DIR):
        raise HTTPException(status_code=404, detail='Data directory not found')

    # Security check: ensure filename does not contain path separators
    if os.path.sep in filename or '..' in filename:
         raise HTTPException(status_code=400, detail='Invalid filename')

    file_path = os.path.join(RG_DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail='File not found')

    return FileResponse(file_path, filename=filename, media_type='text/csv')

@router.delete('/map/files/{filename}')
def delete_map_file(filename: str):
    if not os.path.exists(RG_DATA_DIR):
        raise HTTPException(status_code=404, detail='Data directory not found')

    # Security check: ensure filename does not contain path separators
    if os.path.sep in filename or '..' in filename:
         raise HTTPException(status_code=400, detail='Invalid filename')

    file_path = os.path.join(RG_DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail='File not found')

    try:
        os.remove(file_path)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f'Error deleting file: {e}')

    return {"status": "success", "filename": filename}
