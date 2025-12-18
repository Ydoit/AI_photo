import asyncio
import logging
import os
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models.task import Task, TaskStatus
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

async def handle_extract_metadata(task_manager, task: Task, db: Session):
    """
    Handle single file metadata extraction (Heavy task: Geolocation etc.)
    """
    file_path = task.payload.get('file_path')
    photo_id_str = task.payload.get('photo_id')
    if not file_path or not photo_id_str:
        return {'status': 'skipped', 'reason': 'missing args'}
    # Check if photo still exists
    try:
        photo_id = UUID(photo_id_str)
    except:
        return {'status': 'failed', 'reason': 'invalid uuid'}

    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
         return {'status': 'skipped', 'reason': 'photo not found'}
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(
        task_manager.process_pool,
        rebuild_metadata_cpu_job,
        file_path,
        photo_id
    )
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

    query = db.query(Photo)
    all_photos = query.all()
    photos = []

    # Filter by processed status
    for p in all_photos:
        if force:
            photos.append(p)
        else:
            tasks_status = p.processed_tasks or {}
            if not tasks_status.get('metadata'):
                photos.append(p)

    task.total_items = len(photos)
    task.processed_items = 0
    db.commit()

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
            res = await loop.run_in_executor(
                task_manager.process_pool,
                rebuild_metadata_cpu_job,
                photo.file_path,
                photo.id
            )
            if res['success']:
                meta = res['meta']
                # Update DB
                # Check if metadata exists
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
            else:
                errors += 1
        except Exception as e:
            errors += 1
            logging.error(f"Metadata rebuild error for {photo.id}: {e}")
        processed += 1
