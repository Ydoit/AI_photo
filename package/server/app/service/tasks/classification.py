import logging
import os
import aiohttp
from aiohttp import FormData
import json
from sqlalchemy.orm import Session
from app.db.models.task import Task, TaskType
from app.db.models.photo import Photo, FileType
from typing import Dict, Any, List
from app.core.config_manager import config_manager
from app.crud import tag as crud_tag
from app.crud import crud_vector
from PIL import Image

logger = logging.getLogger(__name__)

async def handle_classification_task(task_manager, task: Task, db: Session) -> Dict[str, Any]:
    """
    Handle Image Classification task
    """
    try:
        force = task.payload.get('force', False)
        
        # 1. Single Photo Mode
        if task.payload and 'photo_id' in task.payload:
            photo_id = task.payload['photo_id']
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                return {'status': 'skipped', 'reason': 'photo not found'}
            
            # Check if already processed (unless force)
            if not force:
                tasks_status = photo.processed_tasks or {}
                if tasks_status.get('classification'):
                     return {'status': 'skipped', 'reason': 'already processed'}

            return await process_single_photo(task_manager, photo, db)

        # 2. Generator Mode (Scan all)
        photos_to_process = []
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
                    if not tasks_status.get('classification'):
                        should_process = True
                
                if should_process:
                    tasks_to_create.append({
                        'type': TaskType.CLASSIFY_IMAGE,
                        'payload': {'photo_id': str(p.id), 'force': force},
                        'priority': 1
                    })

            if tasks_to_create:
                task_manager.add_tasks(db, tasks_to_create)
                generated_count += len(tasks_to_create)

            offset += batch_size

        return {
            'processed': 0,
            'generated_tasks': generated_count,
            'message': f'Generated {generated_count} Classification tasks'
        }

    except Exception as e:
        logger.error(f"Classification task failed: {e}")
        raise e

async def process_single_photo(task_manager, photo: Photo, db: Session) -> Dict[str, Any]:
    from app.service import storage

    try:
        # 1. Resolve file path
        # Use preview for speed if available, otherwise original
        target_path = storage.get_preview_path(photo.id, db)
        if not os.path.exists(target_path):
            target_path = photo.file_path
            if not target_path or not os.path.exists(target_path):
                return {'status': 'failed', 'error': 'file not found'}

        async with aiohttp.ClientSession() as session:
            # 1. Read file
            with open(target_path, 'rb') as f:
                file_data = f.read()

            form_data = FormData()
            form_data.add_field(
                name='file',
                value=file_data,
                filename=photo.filename,
                content_type='image/jpeg'
            )

            # 2. Call AI Service
            api_url = f"{config_manager.config.ai.ai_api_url}/classification/classify"
            # Optional parameters can be added to query string if needed
            
            async with session.post(
                api_url,
                data=form_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    # Response structure:
                    # {
                    #   "results": [{"label": "...", "confidence": ...}, ...],
                    #   "embedding": [0.1, ...]
                    # }
                    classification_results = result.get('results', [])
                    embedding = result.get('embedding', [])
                    # 2. Process Results
                    # Remove existing AI tags
                    crud_tag.remove_tags_from_photo(db, photo.id, ai_generated=True)
                    # 3. Save Tags
                    tags_added = 0
                    for item in classification_results:
                        label = item.get('label')
                        confidence = item.get('confidence', 0.0)
                        if confidence < config_manager.config.ai.classification_tag_threshold:
                            continue
                        # Add tag
                        if label:
                            crud_tag.add_tag_to_photo(db, photo.id, label, confidence)
                            tags_added += 1

                    # 4. Save Embedding
                    if embedding:
                        crud_vector.create_or_update_vector(db, photo.id, embedding)

                    # 5. Update Status
                    tasks_status = dict(photo.processed_tasks or {})
                    tasks_status['classification'] = True
                    photo.processed_tasks = tasks_status
                    db.add(photo)
                    db.commit()

                    return {
                        'status': 'success',
                        'tags_added': tags_added,
                        'embedding_saved': bool(embedding)
                    }
                else:
                    return {'status': 'failed', 'error': f"AI Service error: {resp.status}"}
    except Exception as e:
        logger.error(f"Error processing classification for photo {photo.id}: {e}")
        tasks_status = dict(photo.processed_tasks or {})
        tasks_status['classification'] = False
        photo.processed_tasks = tasks_status
        db.add(photo)
        db.commit()
        raise e
