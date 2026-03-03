from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.service import indexer
from app.db.models.index_log import IndexLog
from app.api.deps import get_current_user
from app.db.models.user import User

router = APIRouter()

@router.post('/rebuild')
def rebuild(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    indexer.rebuild_index(db, user_id=str(current_user.id))
    return {'started': True}

from app.service.task_manager import TaskManager

@router.get('/status')
def status():
    return TaskManager.get_instance().get_status()

@router.get('/logs')
def logs(limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(IndexLog).order_by(IndexLog.id.desc()).limit(limit).all()
    return [
        {
            'id': i.id,
            'action': i.action,
            'file_path': i.file_path,
            'photo_id': str(i.photo_id) if i.photo_id else None,
            'details': i.details,
            'created_at': i.created_at
        } for i in q
    ]

