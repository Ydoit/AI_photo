import asyncio
import logging
import os
import json
import concurrent.futures
from typing import Set
from uuid import UUID, uuid4
from PIL import Image
from sqlalchemy.orm import Session

from app.db.models.task import Task, TaskType, TaskStatus
from app.db.models.photo import ImageType, Photo, FileType
from app.db.models.index_log import IndexLog
from app.schemas.metadata import PhotoMetadataCreate
from app.service import storage
from app.utils import exif
from app.schemas import album as album_schemas
from app.schemas import photo as photo_schemas
from app.core.config_manager import config_manager
from app.service.live_photo import live_photo_service

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
        if ext in ('.png', '.jpg', '.jpeg', '.webp', '.heic'):
             try:
                 image_obj = Image.open(file_path)
             except Exception:
                 pass

        # 1. Generate thumbnail
        thumb_path = storage.generate_thumbnail(file_path, file_id, db=None, image_obj=image_obj)

        # 2. Extract metadata (BASIC ONLY)
        file_name = os.path.basename(file_path)
        meta = exif.extract_metadata(file_path, file_name, image_obj=image_obj, extract_location_details=False)
        if meta.get("exif_info"):
            # Serialize for storage
            # Convert non-serializable objects to string
            def default_serializer(obj):
                if isinstance(obj, (bytes, bytearray)):
                    return str(obj)
                return str(obj)
            meta['exif_info'] = json.dumps(meta["exif_info"], default=default_serializer, ensure_ascii=False)
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

    EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.tiff', '.gif', '.mp4', '.mov', '.avi', '.heic'}
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
    live_photo_files = set()
    live_photo_to_add = set()
    for p in db.query(Photo.file_path, Photo.file_type).all():
        if p[1] == FileType.live_photo:
            if p[0].endswith('.jpg'):
                live_photo_files.add(p[0])
        elif p[0].endswith('.jpg') and (p[0][:-3] + 'mp4' in existing_files):
            live_photo_to_add.add(p[0])
        elif p[0].endswith('.mp4') and (p[0][:-4] + '.jpg' in existing_files):
            live_photo_to_add.add(p[0])
        existing_files.add(p[0])

    # Determine new and deleted
    new_files = files_on_disk - existing_files
    deleted_files = existing_files - files_on_disk

    for lp in live_photo_files:
        video_path = lp[:-3] + 'mp4'
        if (lp not in files_on_disk) and (video_path not in files_on_disk):
            deleted_files.add(lp)
        elif (lp in files_on_disk) and (video_path not in files_on_disk):
            deleted_files.add(lp)
            new_files.add(lp)
        elif (lp not in files_on_disk) and (video_path in files_on_disk):
            deleted_files.add(lp)
            new_files.add(video_path)
        elif (lp in files_on_disk) and (video_path in files_on_disk):
            new_files.remove(video_path)
    for lp in live_photo_to_add:
        if lp.endswith('.jpg'):
            deleted_files.add(lp[:-3] + 'mp4')
            new_files.add(lp[:-3] + 'mp4')
        else:
            deleted_files.add(lp[:-3] + 'jpg')
            new_files.add(lp[:-3] + 'jpg')
        new_files.add(lp)
        deleted_files.add(lp)
    # 1. 数据库里有实况图但是图片和视频都被删了
    # 2. 数据库里有实况图但是图片被删了
    # 3. 数据库里有实况图但是视频被删了

    logging.info(f"Scan result: {len(new_files)} new, {len(deleted_files)} deleted")
    task_manager.scan_status['message'] = f"Found {len(new_files)} new, {len(deleted_files)} deleted"
    task_manager.scan_status['total_files'] += len(new_files)

    # Queue process tasks for new files
    new_tasks = []
    # Group files to identify Live Photos
    grouped_files = {}
    for fp in new_files:
        dirname, basename = os.path.split(fp)
        name, ext = os.path.splitext(basename)
        key = (dirname, name)
        if key not in grouped_files:
            grouped_files[key] = {}
        grouped_files[key][ext.lower()] = fp

    processed_paths = set()

    for key, files in grouped_files.items():
        image_path = None
        video_path = None

        # Identify candidates for Live Photos
        if '.heic' in files:
            image_path = files['.heic']
        elif '.jpg' in files:
            image_path = files['.jpg']
        elif '.jpeg' in files:
            image_path = files['.jpeg']

        if '.mov' in files:
            video_path = files['.mov']
        elif '.mp4' in files:
            video_path = files['.mp4']

        is_live = False
        final_video_path = None

        try:
            # Logic 1: Apple Live Photo (HEIC based)
            # If it's a HEIC file, we trust the metadata if present.
            if image_path and image_path.lower().endswith('.heic'):
                cid = await loop.run_in_executor(None, live_photo_service.get_content_identifier, image_path)
                if cid:
                    is_live = True
                    # If we have a video file (e.g. .mov), we associate it, but it's not strictly required for detection
                    # per user instruction "Apple is single .HEIC file"
                    if video_path:
                        final_video_path = video_path

            # Logic 2: Android/Other Live Photo (Pair based)
            # Must have both Image and Video, and they must share the Content Identifier
            elif image_path and video_path:
                 def check_live_pair(img, vid):
                     cid1 = live_photo_service.get_content_identifier(img)
                     cid2 = live_photo_service.get_content_identifier(vid)
                     return cid1 and cid2 and cid1 == cid2
                 
                 if await loop.run_in_executor(None, check_live_pair, image_path, video_path):
                     is_live = True
                     final_video_path = video_path

        except Exception as e:
            logging.error(f"Error checking live photo for {image_path}: {e}")

        if is_live:
            new_tasks.append(Task(
                type=TaskType.PROCESS_BASIC,
                payload={
                    'file_path': image_path,
                    'live_photo_video_path': final_video_path,
                    'is_live_photo': True
                },
                priority=10,
                status=TaskStatus.PENDING
            ))
            processed_paths.add(image_path)
            if final_video_path:
                processed_paths.add(final_video_path)

        # Add remaining files as individual tasks
        for ext, fp in files.items():
            if fp not in processed_paths:
                new_tasks.append(Task(
                    type=TaskType.PROCESS_BASIC,
                    payload={'file_path': fp},
                    priority=10,
                    status=TaskStatus.PENDING
                ))
                processed_paths.add(fp)

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
    live_photo_video_path = task.payload.get('live_photo_video_path')
    is_live_photo = task.payload.get('is_live_photo', False)
    if not file_path or not os.path.exists(file_path):
        return {'status': 'skipped', 'reason': 'file not found'}

    photo_id = uuid4()
    storage_root = storage._get_storage_root(db)

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        task_manager.thread_pool,
        process_basic_cpu_job,
        file_path,
        photo_id,
        storage_root
    )
    # result = process_basic_cpu_job(file_path, photo_id, storage_root)
    if not result['success']:
        raise Exception(result.get('error', 'Unknown error'))

    # Construct PhotoCreate data for bulk insert in TaskManager
    meta = result['meta']
    ext = os.path.splitext(result['file_name'])[1]
    file_type = FileType.image
    if ext.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
        file_type = FileType.video
    
    if is_live_photo:
        file_type = FileType.live_photo
    elif live_photo_video_path:
        file_type = FileType.live_photo

    # We need to return raw data, not schemas, because bulk_create_photos expects dicts or similar?
    # Actually album_crud.batch_create_photos expects schemas.PhotoCreate
    photo_create = photo_schemas.PhotoCreate(
        file_type=file_type,
        size=result['size'],
        width=result['width'],
        height=result['height'],
        duration=result['duration'],
        filename=result['file_name'],
        photo_time=meta["photo_time"],
        live_photo_video_path=live_photo_video_path if file_type == FileType.live_photo else None
    )

    metadata_create = PhotoMetadataCreate(
        exif_info=meta["exif_info"],
        # Basic task doesn't have location details yet
    )

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
