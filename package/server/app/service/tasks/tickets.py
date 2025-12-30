import logging
import os
import aiohttp
from aiohttp import FormData
from sqlalchemy.orm import Session
from app.db.models.task import Task, TaskType
from app.db.models.photo import Photo, FileType
from typing import Dict, Any, List
from app.core.config_manager import config_manager
from app.service import storage

logger = logging.getLogger(__name__)

async def handle_ticket_task(task_manager, task: Task, db: Session) -> Dict[str, Any]:
    try:
        force = task.payload.get('force', False)
        
        if task.payload and 'photo_id' in task.payload:
            photo_id = task.payload['photo_id']
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                return {'status': 'skipped', 'reason': 'photo not found'}
            
            if not force:
                tasks_status = photo.processed_tasks or {}
                if tasks_status.get('tickets'):
                     return {'status': 'skipped', 'reason': 'already processed'}

            return await process_single_photo(task_manager, photo, db)

        # Generator Mode
        batch_size = 1000
        offset = 0
        generated_count = 0
        
        while True:
            batch = db.query(Photo).offset(offset).limit(batch_size).all()
            if not batch:
                break

            tasks_to_create = []
            for p in batch:
                if p.file_type == FileType.video:
                    continue
                
                should_process = False
                if force:
                    should_process = True
                else:
                    tasks_status = p.processed_tasks or {}
                    if not tasks_status.get('tickets'):
                        should_process = True
                
                if should_process:
                    tasks_to_create.append({
                        'type': TaskType.RECOGNIZE_TICKET,
                        'payload': {'photo_id': str(p.id), 'force': force},
                        'priority': 2
                    })

            if tasks_to_create:
                task_manager.add_tasks(db, tasks_to_create)
                generated_count += len(tasks_to_create)

            offset += batch_size

        return {
            'processed': 0,
            'generated_tasks': generated_count,
            'message': f'Generated {generated_count} ticket recognition tasks'
        }

    except Exception as e:
        logger.error(f"Ticket task failed: {e}")
        raise e

async def process_single_photo(task_manager, photo: Photo, db: Session) -> Dict[str, Any]:
    try:
        target_path = storage.get_preview_path(photo.id, db)
        if not os.path.exists(target_path):
            target_path = photo.file_path
            if not target_path or not os.path.exists(target_path):
                return {'status': 'failed', 'error': 'file not found'}

        async with aiohttp.ClientSession() as session:
            with open(target_path, 'rb') as f:
                file_data = f.read()

            form_data = FormData()
            form_data.add_field(
                name='file',
                value=file_data,
                filename=photo.filename,
                content_type='image/jpeg'
            )

            api_url = f"{config_manager.config.ai.ai_api_url}/tickets/predict"
            
            async with session.post(api_url, data=form_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Update processed status
                    tasks_status = photo.processed_tasks or {}
                    tasks_status['tickets'] = True
                    photo.processed_tasks = tasks_status
                    
                    # NOTE: Here we could save the structured ticket info to a DB table if one existed.
                    # For now, the result is returned and will be stored in Task.result
                    # logger.info(f"Ticket task result for photo {photo.id}: {result}")
                    
                    db.add(photo)
                    db.commit()
                    
                    return result
                else:
                    text = await response.text()
                    logger.error(f"AI Service error: {response.status} {text}")
                    raise Exception(f"AI Service error: {response.status}")

    except Exception as e:
        logger.error(f"Process ticket failed: {e}")
        raise e

def release_resources():
    pass
