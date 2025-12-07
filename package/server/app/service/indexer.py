import os
import json
from typing import Dict, Set
from sqlalchemy.orm import Session
from app.db.models.app_setting import AppSetting
from app.db.models.photo import Photo, FileType
from app.db.models.index_log import IndexLog
from app.crud import album as crud
from app.api import album as album_api
from uuid import uuid4

status: Dict[str, any] = {
    'running': False,
    'progress': 0.0,
    'added': 0,
    'deleted': 0,
    'errors': 0
}

EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.tiff', '.gif', '.mp4', '.mov', '.avi'}

def _storage_root(db: Session) -> str:
    s = db.query(AppSetting).filter(AppSetting.key == 'storage_root').first()
    return s.value if s and s.value else 'uploads'

def rebuild_index(db: Session):
    if status.get('running'):
        return
    status.update({'running': True, 'progress': 0.0, 'added': 0, 'deleted': 0, 'errors': 0})
    try:
        root = _storage_root(db)
        primary_uploads = os.path.join(root, 'uploads')
        
        ext_setting = db.query(AppSetting).filter(AppSetting.key == 'external_directories').first()
        external_dirs = []
        if ext_setting and ext_setting.value:
            try:
                external_dirs = json.loads(ext_setting.value)
            except:
                pass
        
        scan_roots = [primary_uploads] + external_dirs
        
        existing: Set[str] = set()
        for p in db.query(Photo.file_path).all():
            existing.add(p[0])
            
        files: Set[str] = set()
        total = 0
        
        for base in scan_roots:
            if os.path.isdir(base):
                for dirpath, _, filenames in os.walk(base):
                    for fn in filenames:
                        ext = os.path.splitext(fn)[1].lower()
                        if ext in EXTS:
                            fp = os.path.join(dirpath, fn)
                            files.add(fp)
                            total += 1
                            
        processed = 0
        for fp in files:
            processed += 1
            if fp not in existing:
                try:
                    pid = uuid4()
                    album_api._save_and_create_photo(db, fp, os.path.basename(fp), None, pid)
                    db.add(IndexLog(action='added', file_path=fp, photo_id=pid))
                    db.commit()
                    status['added'] += 1
                except Exception:
                    status['errors'] += 1
            status['progress'] = processed / max(total, 1)
        to_delete = existing - files
        for fp in to_delete:
            try:
                ph = db.query(Photo).filter(Photo.file_path == fp).first()
                if ph:
                    db.delete(ph)
                    db.add(IndexLog(action='deleted', file_path=fp, photo_id=ph.id))
                    db.commit()
                    status['deleted'] += 1
            except Exception:
                status['errors'] += 1
        status['progress'] = 1.0
    finally:
        status['running'] = False

