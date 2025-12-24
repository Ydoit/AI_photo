import asyncio
import logging
import os
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models.task import Task, TaskStatus, TaskType
from app.db.models.photo import Photo
from app.db.models.photo_metadata import PhotoMetadata
from app.utils import exif

def rebuild_metadata_cpu_job(file_path: str, file_id: UUID):
    try:
        file_name = os.path.basename(file_path)
        # Defaults to extract_location_details=True
        meta = exif.extract_metadata(file_path, file_name)
        return {"success": True, "meta": meta}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def sync_rebuild_metadata_cpu_job(file_path: str, file_id: UUID):
    try:
        file_name = os.path.basename(file_path)
        # Defaults to extract_location_details=True
        meta = exif.extract_metadata(file_path, file_name)
        return {"success": True, "meta": meta}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def handle_extract_metadata(task_manager, task: Task, db: Session):
    """
    Handle single file metadata extraction (Heavy task: Geolocation etc.)
    """
    photo_id_str = task.payload.get('photo_id')
    if not photo_id_str:
        return {'status': 'skipped', 'reason': 'missing photo_id'}

    # Check if photo still exists
    try:
        photo_id = UUID(photo_id_str)
    except:
        return {'status': 'failed', 'reason': 'invalid uuid'}

    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
         return {'status': 'skipped', 'reason': 'photo not found'}

    file_path = task.payload.get('file_path')
    if not file_path:
        file_path = photo.file_path

    loop = asyncio.get_running_loop()
    # res = await loop.run_in_executor(
    #     task_manager.thread_pool,
    #     rebuild_metadata_cpu_job,
    #     file_path,
    #     photo_id
    # )
    # res = rebuild_metadata_cpu_job(file_path,photo_id)
    res = await sync_rebuild_metadata_cpu_job(file_path, photo_id)
    if res['success']:
        meta = res['meta']
        # Update DB
        db_meta = db.query(PhotoMetadata).filter(PhotoMetadata.photo_id == photo.id).first()
        if not db_meta:
            db_meta = PhotoMetadata(photo_id=photo.id)
            db.add(db_meta)

        # Update fields
        if meta.get("exif_info"):
            db_meta.exif_info = meta["exif_info"]

        loc_details = meta.get("location_details", {})
        if loc_details:
            if loc_details.get("longitude"): db_meta.longitude = loc_details.get("longitude")
            if loc_details.get("latitude"): db_meta.latitude = loc_details.get("latitude")
            if loc_details.get("city"): db_meta.city = loc_details.get("city")
            if loc_details.get("district"): db_meta.district = loc_details.get("district")
            if loc_details.get("province"): db_meta.province = loc_details.get("province")
            if loc_details.get("country"): db_meta.country = loc_details.get("country")
            if loc_details.get("address"): db_meta.address = loc_details.get("address")

        if meta.get("photo_time"):
            photo.photo_time = meta["photo_time"]

        # Mark as processed
        tasks_status = dict(photo.processed_tasks or {})
        tasks_status['metadata'] = True
        photo.processed_tasks = tasks_status
        db.add(photo)
        db.commit()
        return {'status': 'success'}
    else:
        raise Exception(res.get('error'))

async def handle_rebuild_metadata(task_manager, task: Task, db: Session):
    scope = task.payload.get('scope', 'all')
    force = task.payload.get('force', False)

    # Generator Mode: Create EXTRACT_METADATA tasks for each photo
    batch_size = 1000
    offset = 0
    generated_count = 0

    while True:
        batch = db.query(Photo).offset(offset).limit(batch_size).all()
        if not batch:
            break

        tasks_to_create = []
        for p in batch:
            should_process = False
            if force:
                should_process = True
            else:
                tasks_status = p.processed_tasks or {}
                if not tasks_status.get('metadata'):
                    should_process = True

            if should_process:
                tasks_to_create.append({
                    'type': TaskType.EXTRACT_METADATA,
                    'payload': {'photo_id': str(p.id), 'file_path': p.file_path}, # Pass file_path for optimization
                    'priority': 5
                })

        if tasks_to_create:
            task_manager.add_tasks(db, tasks_to_create)
            generated_count += len(tasks_to_create)

        offset += batch_size

    return {
        'processed': 0,
        'generated_tasks': generated_count,
        'message': f'Generated {generated_count} metadata extraction tasks'
    }

def release_resources():
    import reverse_geocoder as rg
    rg.unload()