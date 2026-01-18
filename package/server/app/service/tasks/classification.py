import logging
import os
import aiohttp
from aiohttp import FormData
from sqlalchemy.orm import Session
from app.db.models.task import Task, TaskType
from app.db.models.photo import Photo, FileType
from app.db.models.tag import PhotoTag, PhotoTagRelation
from app.db.models.image_vector import ImageVector
from typing import Dict, Any, List
from app.core.config_manager import config_manager
from app.crud import tag as crud_tag

from app.service import storage

logger = logging.getLogger(__name__)

async def handle_classify_image(task_manager, task: Task, db: Session) -> Dict[str, Any]:
    try:
        force = task.payload.get('force', False)
        
        if task.payload and 'photo_id' in task.payload:
            photo_id = task.payload['photo_id']
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                return {'status': 'skipped', 'reason': 'photo not found'}
            
            if not force:
                tasks_status = photo.processed_tasks or {}
                if tasks_status.get('classification'):
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
                    if not tasks_status.get('classification'):
                        should_process = True
                
                if should_process:
                    tasks_to_create.append({
                        'type': TaskType.CLASSIFY_IMAGE,
                        'payload': {'photo_id': str(p.id), 'force': force},
                        'priority': 3
                    })

            if tasks_to_create:
                task_manager.add_tasks(db, tasks_to_create)
                generated_count += len(tasks_to_create)

            offset += batch_size

        return {
            'processed': 0,
            'generated_tasks': generated_count,
            'message': f'Generated {generated_count} classification tasks'
        }

    except Exception as e:
        logger.error(f"Classification task failed: {e}")
        raise e

async def process_single_photo(task_manager, photo: Photo, db: Session) -> Dict[str, Any]:
    try:
        target_path = storage.get_preview_path(photo.id)
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

            api_url = f"{config_manager.config.ai.ai_api_url}/classification/classify"
            async with session.post(api_url, data=form_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    results = result.get('results', [])
                    embedding = result.get('embedding', [])
                    crud_tag.remove_tags_from_photo(db, photo.id, ai_generated=True)

                    # Save Embedding
                    vector = db.query(ImageVector).filter(ImageVector.photo_id == photo.id).first()
                    if not vector:
                        vector = ImageVector(photo_id=photo.id)
                        db.add(vector)
                    vector.embedding = embedding

                    # Save Tags
                    for res in results:
                        tag_name = res['label']
                        confidence = res['confidence']
                        if confidence < config_manager.config.ai.classification_tag_threshold:
                            continue
                        tag = db.query(PhotoTag).filter(PhotoTag.tag_name == tag_name).first()
                        if not tag:
                            tag = PhotoTag(tag_name=tag_name)
                            db.add(tag)
                            db.flush() # get id
                        
                        # Check relation
                        rel = db.query(PhotoTagRelation).filter(
                            PhotoTagRelation.photo_id == photo.id,
                            PhotoTagRelation.tag_id == tag.id
                        ).first()
                        
                        if not rel:
                            rel = PhotoTagRelation(photo_id=photo.id, tag_id=tag.id, confidence=confidence)
                            db.add(rel)
                        else:
                            rel.confidence = confidence

                    tasks_status = dict(photo.processed_tasks or {})
                    tasks_status['classification'] = True
                    photo.processed_tasks = tasks_status
                    db.add(photo)
                    db.commit()
                    return {'status': 'success', 'tags_found': len(results)}
                else:
                    return {'status': 'failed', 'error': f"AI Service error: {resp.status}"}
    except Exception as e:
        logger.error(f"Error processing Classification for photo {photo.id}: {e}")
        tasks_status = dict(photo.processed_tasks or {})
        tasks_status['classification'] = False
        photo.processed_tasks = tasks_status
        db.add(photo)
        db.commit()
        raise e

def release_resources():
    pass
