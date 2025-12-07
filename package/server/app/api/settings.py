from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import tempfile
import json
from app.dependencies import get_db
from app.db.models.app_setting import AppSetting
from app.db.models.photo import Photo
from app.service.storage import delete_thumbnails
from app.service.indexer import rebuild_index as service_rebuild_index, status as index_status
from app.db.models.index_log import IndexLog

router = APIRouter()

def get_storage_root(db: Session) -> str:
    setting = db.query(AppSetting).filter(AppSetting.key == 'storage_root').first()
    if setting and setting.value:
        return setting.value
    return 'uploads'

def get_external_dirs(db: Session) -> list[str]:
    setting = db.query(AppSetting).filter(AppSetting.key == 'external_directories').first()
    if setting and setting.value:
        try:
            return json.loads(setting.value)
        except:
            return []
    return []

@router.get('/settings/directories')
def get_directories(db: Session = Depends(get_db)):
    primary = get_storage_root(db)
    external = get_external_dirs(db)
    return {'primary': primary, 'external': external}

@router.post('/settings/directories')
def add_directory(payload: dict, db: Session = Depends(get_db)):
    path = payload.get('path')
    if not path or not isinstance(path, str):
        raise HTTPException(status_code=400, detail='invalid path')
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail='not a directory')
    
    current = get_external_dirs(db)
    if path in current:
        return {'primary': get_storage_root(db), 'external': current}
    
    # Check if writable not strictly required for external (read-only), but good practice if we ever write metadata
    # For now, let's just ensure it exists.
    
    current.append(path)
    
    setting = db.query(AppSetting).filter(AppSetting.key == 'external_directories').first()
    if not setting:
        setting = AppSetting(key='external_directories', value=json.dumps(current))
        db.add(setting)
    else:
        setting.value = json.dumps(current)
    db.commit()
    
    return {'primary': get_storage_root(db), 'external': current}

@router.delete('/settings/directories')
def remove_directory(payload: dict, db: Session = Depends(get_db)):
    path = payload.get('path')
    if not path:
        raise HTTPException(status_code=400, detail='path required')
    
    current = get_external_dirs(db)
    if path in current:
        current.remove(path)
        setting = db.query(AppSetting).filter(AppSetting.key == 'external_directories').first()
        if setting:
            setting.value = json.dumps(current)
            db.add(setting) # ensure update
            
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

@router.get('/settings/storage-root')
def read_storage_root(db: Session = Depends(get_db)):
    return {'storage_root': get_storage_root(db)}

@router.put('/settings/storage-root')
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
    setting = db.query(AppSetting).filter(AppSetting.key == 'storage_root').first()
    if not setting:
        setting = AppSetting(key='storage_root', value=path)
        db.add(setting)
    else:
        setting.value = path
    db.commit()
    return {'storage_root': path}

