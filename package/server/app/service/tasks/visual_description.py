import logging
import os
import json
import base64
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from app.db.models.task import Task, TaskType
from app.db.models.photo import Photo, FileType
from app.db.models.image_description import ImageDescription
from app.core.config_manager import config_manager
from app.service import storage

logger = logging.getLogger(__name__)

async def handle_visual_description_task(task_manager, task: Task, db: Session) -> Dict[str, Any]:
    """
    Handle Visual Description task
    """
    try:
        # Check configuration
        settings = config_manager.config.ai.llm_vl_settings
        if not settings.base_url or not settings.api_key or not settings.model_name:
             return {'status': 'skipped', 'reason': 'Visual Model not configured'}

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
                if tasks_status.get('visual_description'):
                     return {'status': 'skipped', 'reason': 'already processed'}

            return await process_single_photo(task_manager, photo, db, settings)

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
                    if not tasks_status.get('visual_description'):
                        should_process = True
                
                if should_process:
                    tasks_to_create.append({
                        'type': TaskType.VISUAL_DESCRIPTION,
                        'payload': {'photo_id': str(p.id), 'force': force},
                        'priority': 3,
                        'owner_id': p.owner_id
                    })

            if tasks_to_create:
                task_manager.add_tasks(db, tasks_to_create)
                generated_count += len(tasks_to_create)

            offset += batch_size

        return {
            'processed': 0,
            'generated_tasks': generated_count,
            'message': f'Generated {generated_count} Visual Description tasks'
        }

    except Exception as e:
        logger.error(f"Visual Description task failed: {e}")
        raise e

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def process_single_photo(task_manager, photo: Photo, db: Session, settings) -> Dict[str, Any]:
    try:
        # 1. Resolve file path
        # Use preview path for smaller size and faster processing, or original if preview missing
        target_path = storage.get_preview_path(photo.id)
        if not os.path.exists(target_path):
            target_path = photo.file_path
            if not target_path or not os.path.exists(target_path):
                return {'status': 'failed', 'error': 'file not found'}

        # 2. Call OpenAI API
        client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=120,
        )

        base64_image = encode_image(target_path)

        prompt = """
        Analyze this image and provide a JSON response with the following fields:
        - description: A short description of the image content in Chinese.
        - quality_score: An integer from 0 to 100 indicating the quality of the photo (focus, lighting, composition).
        - tags: A list of relevant tags (e.g., landscape, person, animal, food, etc.) in Chinese.
        
        Return ONLY the JSON string, no markdown formatting.
        """

        response = await client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=4096,
        )

        content = response.choices[0].message.content
        # Clean up code blocks if present
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]

        result_json = json.loads(content)

        # 3. Save to DB
        # Remove existing if any
        existing = db.query(ImageDescription).filter(ImageDescription.photo_id == photo.id).first()
        if existing:
            db.delete(existing)
            db.flush()

        desc = ImageDescription(
            photo_id=photo.id,
            description=result_json.get("description"),
            quality_score=result_json.get("quality_score"),
            tags=result_json.get("tags")
        )
        db.add(desc)

        # Update photo processed status
        tasks_status = photo.processed_tasks or {}
        tasks_status['visual_description'] = True
        photo.processed_tasks = tasks_status
        
        db.commit()

        return {
            'status': 'completed',
            'description': desc.description,
            'quality': desc.quality_score
        }

    except Exception as e:
        logger.error(f"Error processing visual description for photo {photo.id}: {e}")
        return {'status': 'failed', 'error': str(e)}
