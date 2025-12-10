import asyncio
import logging
import os
import concurrent.futures
from typing import List, Optional, Set
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import SessionLocal
from app.db.models.task import Task, TaskType, TaskStatus
from app.db.models.photo import Photo, FileType
from app.db.models.app_setting import AppSetting
from app.db.models.index_log import IndexLog
from app.service import storage
from app.utils import exif
from app.schemas import album as album_schemas
from app.crud import album as album_crud

# Process Pool for CPU intensive tasks
# Initialize with available CPU cores
process_pool = concurrent.futures.ProcessPoolExecutor()

def process_image_cpu_job(file_path: str, file_id: UUID, storage_root: str):
    """
    CPU-intensive task running in a separate process.
    Generates thumbnails and extracts metadata.
    """
    try:
        # Initialize storage root cache in this process
        storage.update_storage_root_cache(storage_root)
        
        # 1. Generate thumbnail
        # We pass db=None so it uses the cache we just set
        thumb_path = storage.generate_thumbnail(file_path, file_id, db=None)
        
        # 2. Extract metadata
        file_name = os.path.basename(file_path)
        meta = exif.extract_metadata(file_path, file_name)
        
        # 3. Get dimensions/size
        size = storage.get_file_size(file_path)
        width, height, duration = storage.get_image_dimensions(file_path)
        
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

class TaskManager:
    _instance = None
    
    def __init__(self):
        self.running = False
        self.worker_task = None
        self.scan_status = {
            'running': False,
            'progress': 0.0,
            'added': 0,
            'deleted': 0,
            'errors': 0
        }

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TaskManager()
        return cls._instance

    def start(self):
        if self.running:
            return
        self.running = True
        self.worker_task = asyncio.create_task(self.worker_loop())
        logging.info("TaskManager started")

    def stop(self):
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
        logging.info("TaskManager stopped")

    def add_task(self, db: Session, type: str, payload: dict, priority: int = 0):
        task = Task(type=type, payload=payload, priority=priority)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    async def worker_loop(self):
        logging.info("TaskManager worker loop started")
        active_tasks = set()
        
        while self.running:
            try:
                # Clean up finished tasks
                active_tasks = {t for t in active_tasks if not t.done()}
                
                # Limit concurrency (e.g. 5 concurrent tasks)
                if len(active_tasks) >= 5:
                    await asyncio.sleep(0.2)
                    continue

                # Use a fresh session
                db = SessionLocal()
                try:
                    # Poll for tasks
                    # Prioritize: 1. Priority (desc), 2. Created (asc)
                    task = db.query(Task).filter(Task.status == TaskStatus.PENDING)\
                        .order_by(Task.priority.desc(), Task.created_at.asc())\
                        .first()
                    
                    if task:
                        # Lock task
                        task.status = TaskStatus.PROCESSING
                        db.commit()
                        
                        logging.info(f"Picked task {task.id} ({task.type})")
                        
                        # Launch async wrapper
                        # We don't pass the 'task' object because the session 'db' will be closed
                        future = asyncio.create_task(self.execute_task_wrapper(task.id))
                        active_tasks.add(future)
                    else:
                        # No tasks, sleep briefly
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logging.error(f"Error in worker loop: {e}")
                    await asyncio.sleep(5) # Backoff on DB error
                finally:
                    db.close()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Unexpected error in worker loop: {e}")
                await asyncio.sleep(1)

    async def execute_task_wrapper(self, task_id: UUID):
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return
                
            try:
                result = await self.process_task(task, db)
                task.status = TaskStatus.COMPLETED
                task.result = result
            except Exception as e:
                logging.error(f"Task {task_id} failed: {e}", exc_info=True)
                task.status = TaskStatus.FAILED
                task.error = str(e)
            
            db.commit()
        except Exception as e:
            logging.error(f"Error in task wrapper for {task_id}: {e}")
        finally:
            db.close()

    async def process_task(self, task: Task, db: Session):
        if task.type == TaskType.SCAN_FOLDER:
            return await self.handle_scan_folder(task, db)
        elif task.type == TaskType.PROCESS_IMAGE:
            return await self.handle_process_image(task, db)
        else:
            raise ValueError(f"Unknown task type: {task.type}")

    async def handle_scan_folder(self, task: Task, db: Session):
        # 1. Determine roots
        scan_roots = task.payload.get('scan_roots')
        if not scan_roots:
             # Fetch from DB if not provided
             root = storage._get_storage_root(db)
             primary_uploads = os.path.join(root, 'uploads')
             
             ext_setting = db.query(AppSetting).filter(AppSetting.key == 'external_directories').first()
             external_dirs = []
             if ext_setting and ext_setting.value:
                 import json
                 try:
                     external_dirs = json.loads(ext_setting.value)
                 except:
                     pass
             scan_roots = [primary_uploads] + external_dirs

        EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.tiff', '.gif', '.mp4', '.mov', '.avi'}
        
        # 2. Walk directories (run in thread pool to avoid blocking async loop)
        loop = asyncio.get_running_loop()
        
        def walk_files():
            found_files = set()
            for base in scan_roots:
                if os.path.isdir(base):
                    for dirpath, _, filenames in os.walk(base):
                        for fn in filenames:
                            ext = os.path.splitext(fn)[1].lower()
                            if ext in EXTS:
                                fp = os.path.join(dirpath, fn)
                                found_files.add(fp)
            return found_files

        files_on_disk = await loop.run_in_executor(None, walk_files)
        
        # 3. Get existing files from DB
        existing_files = set()
        for p in db.query(Photo.file_path).all():
            existing_files.add(p[0])
            
        # 4. Determine New and Deleted
        new_files = files_on_disk - existing_files
        deleted_files = existing_files - files_on_disk
        
        logging.info(f"Scan result: {len(new_files)} new, {len(deleted_files)} deleted")
        
        # 5. Create PROCESS_IMAGE tasks for new files
        # We can batch insert tasks for performance
        new_tasks = []
        for fp in new_files:
            new_tasks.append(Task(
                type=TaskType.PROCESS_IMAGE,
                payload={'file_path': fp},
                priority=10, # Higher priority than scan
                status=TaskStatus.PENDING
            ))
            
        if new_tasks:
            db.bulk_save_objects(new_tasks)
            db.commit()
            
        # 6. Handle deletions (can be done immediately or as tasks)
        # Doing immediately for simplicity
        for fp in deleted_files:
            ph = db.query(Photo).filter(Photo.file_path == fp).first()
            if ph:
                db.delete(ph)
                db.add(IndexLog(action='deleted', file_path=fp, photo_id=ph.id))
        db.commit()
        
        return {
            'new_files': len(new_files),
            'deleted_files': len(deleted_files)
        }

    async def handle_process_image(self, task: Task, db: Session):
        file_path = task.payload.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return {'status': 'skipped', 'reason': 'file not found'}
            
        # Create Photo ID
        photo_id = uuid4()
        
        # Get storage root for worker
        storage_root = storage._get_storage_root(db)
        
        # Run CPU intensive work in Process Pool
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            process_pool, 
            process_image_cpu_job, 
            file_path, 
            photo_id, 
            storage_root
        )
        
        if not result['success']:
            raise Exception(result.get('error', 'Unknown error'))
            
        # Save to DB
        meta = result['meta']
        
        # Determine file type
        ext = os.path.splitext(result['file_name'])[1]
        file_type = FileType.image
        if ext.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            file_type = FileType.video

        photo_create = album_schemas.PhotoCreate(
            file_type=file_type,
            size=result['size'],
            width=result['width'],
            height=result['height'],
            duration=result['duration'],
            filename=result['file_name'],
            photo_time=meta["photo_time"]
        )

        metadata_create = album_schemas.PhotoMetadataCreate(
            exif_info=meta["exif_info"],
            location=meta["location"]
        )
        
        # We use album_crud.create_photo but we need to handle album_id if we want auto-grouping
        # Current logic in indexer.py was just create_photo with album_id=None
        
        # Re-implement minimal create_photo logic to avoid complex dependencies or reuse crud
        # reuse crud.create_photo
        album_crud.create_photo(
            db, 
            photo_create, 
            album_id=None, 
            file_path=file_path, 
            photo_id=photo_id, 
            metadata=metadata_create
        )
        
        # Log index
        db.add(IndexLog(action='added', file_path=file_path, photo_id=photo_id))
        
        return {'photo_id': str(photo_id)}
