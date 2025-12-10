import asyncio
import logging
import os
import concurrent.futures
from typing import List, Optional, Set, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from PIL import Image

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
# We will initialize it in TaskManager to avoid side effects on import
# process_pool = concurrent.futures.ProcessPoolExecutor()

def process_image_cpu_job(file_path: str, file_id: UUID, storage_root: str):
    """
    CPU-intensive task running in a separate process.
    Generates thumbnails and extracts metadata.
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
        
        # 2. Extract metadata
        file_name = os.path.basename(file_path)
        meta = exif.extract_metadata(file_path, file_name, image_obj=image_obj)
        
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

class TaskManager:
    _instance = None
    
    def __init__(self):
        self.running = False
        self.worker_task = None
        self.result_task = None
        self.process_pool = None
        self.result_queue = asyncio.Queue()
        self.scan_status = {
            'running': False,
            'progress': 0.0,
            'added': 0,
            'deleted': 0,
            'errors': 0,
            'current_task': None,
            'message': 'Idle',
            'total_files': 0,
            'processed_files': 0
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
        self.process_pool = concurrent.futures.ProcessPoolExecutor()
        self.worker_task = asyncio.create_task(self.worker_loop())
        self.result_task = asyncio.create_task(self.result_loop())
        logging.info("TaskManager started")

    def stop(self):
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
        if self.result_task:
            self.result_task.cancel()
        if self.process_pool:
            self.process_pool.shutdown(wait=False)
            self.process_pool = None
        logging.info("TaskManager stopped")

    def get_status(self):
        return self.scan_status

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
                
                # Update status
                if active_tasks:
                     self.scan_status['running'] = True
                
                # Limit concurrency
                if len(active_tasks) >= 5:
                    await asyncio.sleep(0.1)
                    continue

                db = SessionLocal()
                try:
                    # Poll for tasks
                    task = db.query(Task).filter(Task.status == TaskStatus.PENDING)\
                        .order_by(Task.priority.desc(), Task.created_at.asc())\
                        .first()
                    
                    if task:
                        # Lock task
                        task.status = TaskStatus.PROCESSING
                        db.commit()
                        
                        self.scan_status['current_task'] = f"{task.type} - {task.id}"
                        
                        # Launch async wrapper
                        future = asyncio.create_task(self.execute_task_wrapper(task.id, task.type))
                        active_tasks.add(future)
                    else:
                        if not active_tasks:
                            self.scan_status['running'] = False
                            self.scan_status['message'] = "Idle"
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logging.error(f"Error in worker loop: {e}")
                    await asyncio.sleep(5)
                finally:
                    db.close()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Unexpected error in worker loop: {e}")
                await asyncio.sleep(1)

    async def execute_task_wrapper(self, task_id: UUID, task_type: str):
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return
                
            try:
                result = await self.process_task(task, db)
                
                # Enqueue success result
                await self.result_queue.put({
                    'task_id': task_id,
                    'task_type': task_type,
                    'status': TaskStatus.COMPLETED,
                    'result': result
                })
                
            except Exception as e:
                logging.error(f"Task {task_id} failed: {e}", exc_info=True)
                # Enqueue failure result
                await self.result_queue.put({
                    'task_id': task_id,
                    'task_type': task_type,
                    'status': TaskStatus.FAILED,
                    'error': str(e)
                })
            
        except Exception as e:
            logging.error(f"Error in task wrapper for {task_id}: {e}")
        finally:
            db.close()

    async def result_loop(self):
        logging.info("TaskManager result loop started")
        pending_items = []
        last_flush = datetime.now()
        
        while self.running:
            try:
                try:
                    # Collect items with short timeout
                    item = await asyncio.wait_for(self.result_queue.get(), timeout=0.5)
                    pending_items.append(item)
                except asyncio.TimeoutError:
                    pass
                
                now = datetime.now()
                should_flush = len(pending_items) >= 50 or ((now - last_flush).total_seconds() > 1 and pending_items)
                
                if should_flush:
                    self._flush_results(pending_items)
                    pending_items = []
                    last_flush = now
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in result loop: {e}")
                await asyncio.sleep(1)
                
    def _flush_results(self, items: List[Dict]):
        db = SessionLocal()
        try:
            # 1. Prepare batch photo inserts
            photos_to_create = []
            index_logs = []
            
            for item in items:
                if item['status'] == TaskStatus.COMPLETED and item['task_type'] == TaskType.PROCESS_IMAGE:
                    res = item['result']
                    # res contains 'photo_create_data' which we need to construct
                    if 'photo_create_data' in res:
                        data = res['photo_create_data']
                        photos_to_create.append(data)
                        index_logs.append(IndexLog(action='added', file_path=data['file_path'], photo_id=data['photo_id']))
                        
                        # Update stats
                        self.scan_status['added'] += 1
                        self.scan_status['processed_files'] += 1

            # Batch insert photos
            if photos_to_create:
                album_crud.batch_create_photos(db, photos_to_create)
                db.add_all(index_logs)
                
            # 2. Update tasks
            for item in items:
                task = db.query(Task).filter(Task.id == item['task_id']).first()
                if task:
                    task.status = item['status']
                    if item['status'] == TaskStatus.COMPLETED:
                        # Clear photo_create_data from result to save space in DB
                        res = item.get('result', {})
                        if 'photo_create_data' in res:
                            res = {'photo_id': str(res['photo_create_data']['photo_id'])}
                        task.result = res
                    else:
                        task.error = item.get('error')
                        self.scan_status['errors'] += 1
            
            # Update progress
            if self.scan_status['total_files'] > 0:
                self.scan_status['progress'] = self.scan_status['processed_files'] / self.scan_status['total_files']
                
            db.commit()
            logging.info(f"Flushed {len(items)} task results")
            
        except Exception as e:
            logging.error(f"Error flushing results: {e}")
            db.rollback()
        finally:
            db.close()

    async def process_task(self, task: Task, db: Session):
        if task.type == TaskType.SCAN_FOLDER:
            return await self.handle_scan_folder(task, db)
        elif task.type == TaskType.PROCESS_IMAGE:
            return await self.handle_process_image(task, db)
        else:
            return {'status': 'not_implemented', 'type': task.type}

    async def handle_scan_folder(self, task: Task, db: Session):
        self.scan_status['message'] = "Scanning folders..."
        scan_roots = task.payload.get('scan_roots')
        if not scan_roots:
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
        loop = asyncio.get_running_loop()
        
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
            
        new_files = files_on_disk - existing_files
        deleted_files = existing_files - files_on_disk
        
        logging.info(f"Scan result: {len(new_files)} new, {len(deleted_files)} deleted")
        self.scan_status['message'] = f"Found {len(new_files)} new, {len(deleted_files)} deleted"
        self.scan_status['total_files'] += len(new_files)
        
        new_tasks = []
        for fp in new_files:
            new_tasks.append(Task(
                type=TaskType.PROCESS_IMAGE,
                payload={'file_path': fp},
                priority=10, 
                status=TaskStatus.PENDING
            ))
            
        if new_tasks:
            chunk_size = 1000
            for i in range(0, len(new_tasks), chunk_size):
                db.bulk_save_objects(new_tasks[i:i+chunk_size])
                db.commit()
            
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
                self.scan_status['deleted'] += len(photos_to_delete)
        
        return {'new_files': len(new_files), 'deleted_files': len(deleted_files)}

    async def handle_process_image(self, task: Task, db: Session):
        file_path = task.payload.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return {'status': 'skipped', 'reason': 'file not found'}
            
        photo_id = uuid4()
        storage_root = storage._get_storage_root(db)
        
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            self.process_pool, 
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
        
        # Prepare data for batch insert instead of writing to DB directly
        return {
            'photo_create_data': {
                'photo': photo_create,
                'file_path': file_path,
                'photo_id': photo_id,
                'metadata': metadata_create
            }
        }
