import logging
import aiohttp
import json
from sqlalchemy.orm import Session
from app.db.models.task import Task
from app.db.models.photo import Photo
from app.db.models.face import Face
from app.db.models.task import TaskType
from typing import Dict, Any

AI_SERVICE_URL = "http://localhost:8001"

async def handle_face_recognition(task_manager, task: Task, db: Session) -> Dict[str, Any]:
    """
    Handle face recognition task
    """
    try:
        force = task.payload.get('force', False)
        
        # Get all photos that need face recognition
        # Filter logic: 
        # 1. If payload has photo_id, process that photo
        # 2. Else, process all photos where processed_tasks['face'] is not True (unless force is True)
        
        photos_to_process = []
        if task.payload and 'photo_id' in task.payload:
            photo = db.query(Photo).filter(Photo.id == task.payload['photo_id']).first()
            if photo:
                photos_to_process.append(photo)
        else:
            # Note: JSON querying depends on DB support. 
            # For simplicity in Python filtering:
            # We iterate over photos. For large datasets, this should be optimized with proper SQL JSON queries.
            # Postgres supports: filter(Photo.processed_tasks['face'].astext == 'true')
            # But let's assume we want to process everything not marked true.
            
            # Using basic query and filtering in python for safety if JSON operators vary
            # Ideally: db.query(Photo).filter(func.jsonb_extract_path_text(Photo.processed_tasks, 'face') != 'true').all()
            
            # Optimized for now: Process chunks
            batch_size = 50
            offset = 0
            while True:
                batch = db.query(Photo).offset(offset).limit(batch_size).all()
                if not batch:
                    break
                
                for p in batch:
                    if force:
                        photos_to_process.append(p)
                    else:
                        tasks_status = p.processed_tasks or {}
                        if not tasks_status.get('face'):
                            photos_to_process.append(p)
                
                offset += batch_size
                # Limit total processing per task execution to avoid timeout? 
                # Or just let it run. Let's process all found so far.
                if len(photos_to_process) > 100: # Limit one task run to 100 photos
                    break

        task_manager.scan_status['total_files'] = len(photos_to_process)
        task_manager.scan_status['processed_files'] = 0
        
        processed_count = 0
        error_count = 0
        
        async with aiohttp.ClientSession() as session:
            for photo in photos_to_process:
                try:
                    # 1. Read file
                    with open(photo.file_path, 'rb') as f:
                        file_data = f.read()
                    
                    # 2. Call AI Service
                    async with session.post(
                        f"{AI_SERVICE_URL}/face-recognition", 
                        data={'file': file_data}
                    ) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            faces = result.get('faces', [])
                            
                            # 3. Save Faces
                            for face_data in faces:
                                face = Face(
                                    photo_id=photo.id,
                                    face_feature=face_data['embedding'],
                                    face_rect=face_data['bbox'], # [x1, y1, x2, y2]
                                    face_confidence=face_data['det_score']
                                )
                                db.add(face)
                            
                            # 4. Update Photo Status
                            tasks_status = dict(photo.processed_tasks or {})
                            tasks_status['face'] = True
                            photo.processed_tasks = tasks_status
                            db.add(photo)
                            db.commit()
                            
                            processed_count += 1
                        else:
                            logging.error(f"AI Service error for photo {photo.id}: {resp.status}")
                            error_count += 1
                            
                    task_manager.scan_status['processed_files'] += 1
                    
                except Exception as e:
                    logging.error(f"Error processing photo {photo.id}: {e}")
                    error_count += 1
                    continue

        return {
            'processed': processed_count,
            'errors': error_count,
            'message': 'Face recognition completed'
        }

    except Exception as e:
        logging.error(f"Face recognition task failed: {e}")
        raise e
