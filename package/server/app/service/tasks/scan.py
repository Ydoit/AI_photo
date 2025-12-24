import asyncio
import logging
import os
import concurrent.futures
from typing import Set
from uuid import UUID, uuid4
from PIL import Image
from sqlalchemy.orm import Session

from app.db.models.task import Task, TaskType, TaskStatus
from app.db.models.photo import Photo, FileType
from app.db.models.index_log import IndexLog
from app.schemas.metadata import PhotoMetadataCreate
from app.service import storage
from app.utils import exif
from app.schemas import album as album_schemas
from app.schemas import photo as photo_schemas
from app.core.config_manager import config_manager

def process_basic_cpu_job(file_path: str, file_id: UUID, storage_root: str):
    """
    CPU-intensive task running in a separate process.
    Generates thumbnails and extracts BASIC metadata (no heavy geolocation).
    """
    try:
        # Initialize storage root cache in this process
        storage.update_storage_root_cache(storage_root)
        
        # Open image once if possible to reduce IO
        image_obj = None
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ('.png', '.jpg', '.jpeg', '.webp'):
             try:
                 image_obj = Image.open(file_path)
             except Exception:
                 pass

        # 1. Generate thumbnail
        thumb_path = storage.generate_thumbnail(file_path, file_id, db=None, image_obj=image_obj)

        # 2. Extract metadata (BASIC ONLY)
        file_name = os.path.basename(file_path)
        meta = exif.extract_metadata(file_path, file_name, image_obj=image_obj, extract_location_details=False)

        # 3. Get dimensions/size
        size = storage.get_file_size(file_path)
        width, height, duration = storage.get_image_dimensions(file_path, image_obj=image_obj)

        if image_obj:
            image_obj.close()

        return {
            "success": True,
            "thumb_path": thumb_path,
            "meta": meta,
            "size": size,
            "width": width,
            "height": height,
            "duration": duration,
            "file_name": file_name,
            "photo_create_data": None # Placeholder
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def process_image_cpu_job(file_path: str, file_id: UUID, storage_root: str):
    """
    Legacy/Full processing.
    """
    try:
        storage.update_storage_root_cache(storage_root)
        image_obj = None
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ('.png', '.jpg', '.jpeg', '.webp'):
             try:
                 image_obj = Image.open(file_path)
             except Exception:
                 pass

        thumb_path = storage.generate_thumbnail(file_path, file_id, db=None, image_obj=image_obj)
        file_name = os.path.basename(file_path)
        meta = exif.extract_metadata(file_path, file_name, image_obj=image_obj, extract_location_details=True)
        size = storage.get_file_size(file_path)
        width, height, duration = storage.get_image_dimensions(file_path, image_obj=image_obj)

        if image_obj:
            image_obj.close()

        return {
            "success": True,
            "thumb_path": thumb_path,
            "meta": meta,
            "size": size,
            "width": width,
            "height": height,
            "duration": duration,
            "file_name": file_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def scan_directory_recursive(path: str, exts: Set[str]) -> Set[str]:
    found = set()
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    if os.path.splitext(entry.name)[1].lower() in exts:
                        found.add(entry.path)
                elif entry.is_dir():
                    found.update(scan_directory_recursive(entry.path, exts))
    except OSError:
        pass
    return found

async def handle_scan_folder(task_manager, task: Task, db: Session):
    task_manager.scan_status['message'] = "Scanning folders..."
    scan_roots = task.payload.get('scan_roots')
    if not scan_roots:
            root = storage._get_storage_root(db)
            primary_uploads = os.path.join(root, 'uploads')
            external_dirs = config_manager.config.storage.external_directories
            scan_roots = [primary_uploads] + external_dirs

    EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.tiff', '.gif', '.mp4', '.mov', '.avi'}
    loop = asyncio.get_running_loop()
    logging.info(f"Scanning roots: {scan_roots}")
    def parallel_scan_wrapper():
        found_files = set()
        work_items = []
        for root in scan_roots:
            if not os.path.exists(root):
                continue
            work_items.append(root)
            try:
                with os.scandir(root) as it:
                    for entry in it:
                        if entry.is_dir():
                            work_items.append(entry.path)
            except OSError:
                pass
        work_items = list(set(work_items))
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(scan_directory_recursive, item, EXTS): item for item in work_items}
            for future in concurrent.futures.as_completed(futures):
                found_files.update(future.result())
        return found_files

    files_on_disk = await loop.run_in_executor(None, parallel_scan_wrapper)

    existing_files = set()
    for p in db.query(Photo.file_path).all():
        existing_files.add(p[0])

    # Determine new and deleted
    new_files = files_on_disk - existing_files
    deleted_files = existing_files - files_on_disk

    logging.info(f"Scan result: {len(new_files)} new, {len(deleted_files)} deleted")
    task_manager.scan_status['message'] = f"Found {len(new_files)} new, {len(deleted_files)} deleted"
    task_manager.scan_status['total_files'] += len(new_files)

    # Queue process tasks for new files
    new_tasks = []
    for fp in new_files:
        new_tasks.append(Task(
            type=TaskType.PROCESS_BASIC, # Use Basic Task
            payload={'file_path': fp},
            priority=10, 
            status=TaskStatus.PENDING
        ))

    if new_tasks:
        chunk_size = 1000
        for i in range(0, len(new_tasks), chunk_size):
            db.bulk_save_objects(new_tasks[i:i+chunk_size])
            db.commit()

    # Handle deleted
    if deleted_files:
        deleted_list = list(deleted_files)
        chunk_size = 500
        for i in range(0, len(deleted_list), chunk_size):
            chunk = deleted_list[i:i+chunk_size]
            photos_to_delete = db.query(Photo).filter(Photo.file_path.in_(chunk)).all()
            for ph in photos_to_delete:
                storage.delete_thumbnails(ph.id, db)
                db.delete(ph)
                db.add(IndexLog(action='deleted', file_path=ph.file_path, photo_id=ph.id))
            db.commit()
            task_manager.scan_status['deleted'] += len(photos_to_delete)

    return {'new_files': len(new_files), 'deleted_files': len(deleted_files)}

async def handle_process_basic(task_manager, task: Task, db: Session):
    file_path = task.payload.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return {'status': 'skipped', 'reason': 'file not found'}

    photo_id = uuid4()
    storage_root = storage._get_storage_root(db)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        task_manager.process_pool,
        process_basic_cpu_job,
        file_path,
        photo_id,
        storage_root
    )
    if not result['success']:
        raise Exception(result.get('error', 'Unknown error'))
    
    # Construct PhotoCreate data for bulk insert in TaskManager
    meta = result['meta']
    ext = os.path.splitext(result['file_name'])[1]
    file_type = FileType.image
    if ext.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
        file_type = FileType.video

    # We need to return raw data, not schemas, because bulk_create_photos expects dicts or similar?
    # Actually album_crud.batch_create_photos expects schemas.PhotoCreate
    
    photo_create = photo_schemas.PhotoCreate(
        file_type=file_type,
        size=result['size'],
        width=result['width'],
        height=result['height'],
        duration=result['duration'],
        filename=result['file_name'],
        photo_time=meta["photo_time"]
    )
    
    # Pass metadata separately? No, PhotoCreate doesn't have metadata fields except photo_time
    # We need to pass metadata info too.
    # album_crud.batch_create_photos takes list of {photo: PhotoCreate, metadata: PhotoMetadataCreate}?
    # Let's check album_crud.batch_create_photos. 
    # For now, I will construct a dict that TaskManager can understand.
    
    metadata_create = PhotoMetadataCreate(
        exif_info=meta["exif_info"],
        # Basic task doesn't have location details yet
    )
    
    # Attach ID we generated
    # photo_create doesn't have ID field, but we need to force it to use the one we used for thumbnail
    # So we need to pass it along.
    
    return {
        'photo_create_data': {
            'photo': photo_create,
            'metadata': metadata_create,
            'photo_id': photo_id,
            'file_path': file_path
        }
    }

async def handle_process_image(task_manager, task: Task, db: Session):
    """Legacy handler, keeping for compatibility if needed"""
    file_path = task.payload.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return {'status': 'skipped', 'reason': 'file not found'}

    photo_id = uuid4()
    storage_root = storage._get_storage_root(db)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        task_manager.process_pool,
        process_image_cpu_job,
        file_path,
        photo_id,
        storage_root
    )
    if not result['success']:
        raise Exception(result.get('error', 'Unknown error'))
    meta = result['meta']
    ext = os.path.splitext(result['file_name'])[1]
    file_type = FileType.image
    if ext.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
        file_type = FileType.video

    photo_create = photo_schemas.PhotoCreate(
        file_type=file_type,
        size=result['size'],
        width=result['width'],
        height=result['height'],
        duration=result['duration'],
        filename=result['file_name'],
        photo_time=meta["photo_time"]
    )

    metadata_create = PhotoMetadataCreate(
        exif_info=meta["exif_info"],
    )

    loc_details = meta.get("location_details", {})
    if loc_details:
        metadata_create.longitude = loc_details.get("longitude")
        metadata_create.latitude = loc_details.get("latitude")
        metadata_create.city = loc_details.get("city")
        metadata_create.province = loc_details.get("province")
        metadata_create.country = loc_details.get("country")
        metadata_create.address = loc_details.get("address")
        
    return {
        'photo_create_data': {
            'photo': photo_create,
            'metadata': metadata_create,
            'photo_id': photo_id,
            'file_path': file_path
        }
    }

def release_resources():
    pass
