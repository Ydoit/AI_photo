import logging
import aiohttp
from aiohttp import FormData
import json
from sqlalchemy.orm import Session
from app.db.models.task import Task
from app.db.models.photo import Photo, FileType
from app.db.models.face import Face
from app.db.models.task import TaskType
from typing import Dict, Any

AI_SERVICE_URL = "http://localhost:8001"
FACE_CONFIDENCE_THRESHOLD = 0.75

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
                    if p.file_type == FileType.video:
                        continue
                    if force:
                        photos_to_process.append(p)
                    else:
                        tasks_status = p.processed_tasks or {}
                        if not tasks_status.get('face'):
                            photos_to_process.append(p)

                offset += batch_size
                # Limit total processing per task execution to avoid timeout?
                # Or just let it run. Let's process all found so far.
                # if len(photos_to_process) > 100: # Limit one task run to 100 photos
                #     break
        task.total_items = len(photos_to_process)
        task.processed_items = 0
        db.commit()
        task_manager.scan_status['total_files'] = len(photos_to_process)
        task_manager.scan_status['processed_files'] = 0

        processed = 0
        error_count = 0

        async with aiohttp.ClientSession() as session:
            for photo in photos_to_process:
                try:
                    # 1. Read file
                    with open(photo.file_path, 'rb') as f:
                        file_data = f.read()
                    # 2. 构造multipart/form-data格式的表单（核心修正）
                    form_data = FormData()
                    # 添加文件字段：name='file'（必须和接口的File(...)参数名一致），
                    # value=文件二进制，filename=可选（建议传，模拟真实上传），
                    # content_type=文件MIME类型（适配接口的类型校验）
                    form_data.add_field(
                        name='file',  # 必须和接口的参数名（file: UploadFile）一致
                        value=file_data,
                        filename=photo.filename,  # 可选，建议传（接口可通过filename获取后缀）
                        content_type='image/jpeg'  # 根据实际文件类型设置（如image/png）
                    )

                    # 3. 调用AI服务（用form_data替代原data）
                    async with session.post(
                        f"{AI_SERVICE_URL}/face-recognition",
                        data=form_data,  # 传入构造好的FormData
                        timeout=aiohttp.ClientTimeout(total=30)  # 可选，添加超时保护
                    ) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            faces = result.get('faces', [])
                            # 添加人脸前，先删除该照片已有的人脸数据
                            db.query(Face).filter(Face.photo_id == photo.id).delete()
                            db.commit()
                            # 3. Save Faces
                            for face_data in faces:
                                if face_data['det_score'] < FACE_CONFIDENCE_THRESHOLD:
                                    continue
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
                        else:
                            logging.error(f"AI Service error for photo {photo.id}: {resp.status}")
                            error_count += 1
                    task_manager.scan_status['processed_files'] += 1
                except Exception as e:
                    logging.error(f"Error processing photo {photo.id} ({photo.filename}): {e}")
                    error_count += 1
                    # 4. Update Photo Status
                    tasks_status = dict(photo.processed_tasks or {})
                    tasks_status['face'] = False
                    photo.processed_tasks = tasks_status
                    db.add(photo)
                    db.commit()
                processed += 1
                if processed % 10 == 0:
                    task.processed_items = processed
                    db.commit()
        task.processed_items = processed
        db.commit()

        return {
            'processed': processed,
            'errors': error_count,
            'message': 'Face recognition completed'
        }

    except Exception as e:
        logging.error(f"Face recognition task failed: {e}")
        raise e
