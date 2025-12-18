from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import tempfile
import json
from app.dependencies import get_db
from app.core.config_manager import config_manager
from app.db.models.photo import Photo
from app.service.storage import delete_thumbnails, update_storage_root_cache, _get_storage_root
from app.service.indexer import rebuild_index as service_rebuild_index, status as index_status
from app.db.models.index_log import IndexLog

router = APIRouter()

def get_storage_root(db: Session) -> str:
    return _get_storage_root(db)

def get_external_dirs() -> list[str]:
    return config_manager.config.storage.external_directories

@router.get('/directories')
def get_directories(db: Session = Depends(get_db)):
    primary = get_storage_root(db)
    external = get_external_dirs()
    return {'primary': primary, 'external': external}

@router.post('/directories')
def add_directory(payload: dict, db: Session = Depends(get_db)):
    path = payload.get('path')
    if not path or not isinstance(path, str):
        raise HTTPException(status_code=400, detail='invalid path')
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail='not a directory')
    
    current = get_external_dirs()
    if path in current:
        return {'primary': get_storage_root(db), 'external': current}
    
    current.append(path)
    config_manager.save()
    
    return {'primary': get_storage_root(db), 'external': current}

@router.delete('/directories')
def remove_directory(payload: dict, db: Session = Depends(get_db)):
    path = payload.get('path')
    if not path:
        raise HTTPException(status_code=400, detail='path required')
    
    current = get_external_dirs()
    if path in current:
        current.remove(path)
        config_manager.save()
            
        # Cleanup photos belonging to this directory
        # We need to normalize paths for comparison.
        # Simple string matching with startswith should work if normalized.
        
        # Find photos
        photos = db.query(Photo).all() # Fetching all might be slow but safe for path matching
        # Or use LIKE query
        # photos = db.query(Photo).filter(Photo.file_path.like(f"{path}%")).all()
        # Let's use Python iteration for safety with path separators
        
        norm_path = os.path.normpath(path)
        
        for p in photos:
            if os.path.normpath(p.file_path).startswith(norm_path):
                delete_thumbnails(p.id, db)
                db.delete(p)
                
        db.commit()
        
    return {'primary': get_storage_root(db), 'external': current}

@router.get('/storage-root')
def read_storage_root(db: Session = Depends(get_db)):
    return {'storage_root': get_storage_root(db)}

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
def get_settings():
    return config_manager.get_all()

@router.put('/')
def update_settings(payload: dict):
    config_manager.update_all(payload)
    # Update cache if storage_root changed
    root = config_manager.config.storage.photo_storage_path
    if root:
        update_storage_root_cache(root)
    return {"status": "success", "config": config_manager.get_all()}

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
