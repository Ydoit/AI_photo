import logging
import os
import aiohttp
from aiohttp import FormData
import json
from sqlalchemy.orm import Session
from app.db.models.task import Task
from app.db.models.photo import Photo, FileType
from app.service.face_cluster import FaceClusterService
from app.db.models.task import TaskType
from typing import Dict, Any
from app.core.config_manager import config_manager
from app.crud import face as crud_face
from app.schemas import face as schemas

async def handle_face_recognition(task_manager, task: Task, db: Session) -> Dict[str, Any]:
    """
    Handle face recognition task
    """
    try:
        force = task.payload.get('force', False)
        
        # 1. Single Photo Mode (Worker)
        if task.payload and 'photo_id' in task.payload:
            photo_id = task.payload['photo_id']
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                return {'status': 'skipped', 'reason': 'photo not found'}
            
            # Check if already processed (unless force)
            if not force:
                tasks_status = photo.processed_tasks or {}
                if tasks_status.get('face'):
                     return {'status': 'skipped', 'reason': 'already processed'}

            return await process_single_photo(task_manager, photo, db)

        # 2. Generator Mode (Scan all)
        # Get all photos that need face recognition
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
                    if not tasks_status.get('face'):
                        should_process = True
                
                if should_process:
                    tasks_to_create.append({
                        'type': TaskType.RECOGNIZE_FACE,
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
            'message': f'Generated {generated_count} face recognition tasks'
        }

    except Exception as e:
        logging.error(f"Face recognition task failed: {e}")
        raise e

async def process_single_photo(task_manager, photo: Photo, db: Session) -> Dict[str, Any]:
    cluster_service = FaceClusterService(db)
    from app.service import storage
    
    try:
        # 1. Resolve file path
        target_path = storage.get_preview_path(photo.id, db)
        if not target_path:
            target_path = photo.file_path
        if not os.path.exists(target_path):
             target_path = photo.file_path
             if not os.path.exists(target_path):
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

            # 3. Call AI Service
            async with session.post(
                f"{config_manager.config.ai.ai_api_url}/face-recognition",
                data=form_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    faces = result.get('faces', [])
                    
                    crud_face.delete_faces_by_photo(db, photo.id)
                    
                    for face_data in faces:
                        if face_data['det_score'] < config_manager.config.ai.face_recognition_threshold:
                            continue
                        
                        create_data = schemas.FaceCreate(
                            photo_id=photo.id,
                            face_feature=face_data['embedding'],
                            face_rect=face_data['bbox'],
                            face_confidence=face_data['det_score']
                        )
                        face = crud_face.create_face(db, create_data)

                        if face.face_feature:
                            try:
                                cluster_service.assign_face_to_identity(face.id, face.face_feature)
                            except Exception as ce:
                                logging.error(f"Clustering failed for face {face.id}: {ce}")
                    
                    # Update Status
                    tasks_status = dict(photo.processed_tasks or {})
                    tasks_status['face'] = True
                    photo.processed_tasks = tasks_status
                    db.add(photo)
                    db.commit()
                    
                    task_manager.scan_status['processed_files'] += 1
                    return {'status': 'success', 'faces_found': len(faces)}
                else:
                    return {'status': 'failed', 'error': f"AI Service error: {resp.status}"}
                    
    except Exception as e:
        logging.error(f"Error processing photo {photo.id}: {e}")
        tasks_status = dict(photo.processed_tasks or {})
        tasks_status['face'] = False
        photo.processed_tasks = tasks_status
        db.add(photo)
        db.commit()
        raise e

def release_resources():
    pass