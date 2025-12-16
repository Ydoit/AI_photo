import asyncio
import logging
import os
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models.task import Task, TaskStatus
from app.db.models.photo import Photo
from app.service import storage

def rebuild_thumbnail_cpu_job(file_path: str, file_id: UUID, storage_root: str):
    try:
        storage.update_storage_root_cache(storage_root)
        thumb_path = storage.generate_thumbnail(file_path, file_id, db=None)
        return {"success": True, "thumb_path": thumb_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def handle_rebuild_thumbnails(task_manager, task: Task, db: Session):
    scope = task.payload.get('scope', 'all')
    force = task.payload.get('force', False)
    
    # Determine photos to process
    query = db.query(Photo)
    if scope != 'all':
        pass
        
    all_photos = query.all()
    photos = []
    
    # Filter by processed status
    for p in all_photos:
        if force:
            photos.append(p)
        else:
            tasks_status = p.processed_tasks or {}
            if not tasks_status.get('thumbnail'):
                photos.append(p)
    
    task.total_items = len(photos)
    task.processed_items = 0
    db.commit()
    
    storage_root = storage._get_storage_root(db)
    loop = asyncio.get_running_loop()
    
    processed = 0
    errors = 0
    
    for photo in photos:
        if not task_manager.running:
            break
        
        # Check for cancellation
        db.refresh(task)
        if task.status == TaskStatus.CANCELLED:
            logging.info(f"Task {task.id} cancelled")
            break
            
        try:
            if not os.path.exists(photo.file_path):
                continue

            res = await loop.run_in_executor(
                task_manager.process_pool,
                rebuild_thumbnail_cpu_job,
                photo.file_path,
                photo.id,
                storage_root
            )
            
            if res['success']:
                # Mark as processed
                tasks_status = dict(photo.processed_tasks or {})
                tasks_status['thumbnail'] = True
                photo.processed_tasks = tasks_status
                db.add(photo)
            else:
                errors += 1
                logging.error(f"Thumbnail rebuild failed for {photo.id}: {res.get('error')}")
        except Exception as e:
            errors += 1
            logging.error(f"Thumbnail rebuild error for {photo.id}: {e}")
            
        processed += 1
        if processed % 10 == 0:
            task.processed_items = processed
            db.commit()
            
    task.processed_items = processed
    db.commit()
    
    return {'processed': processed, 'errors': errors, 'total': len(photos)}
