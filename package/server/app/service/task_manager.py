import asyncio
import logging
import concurrent.futures
from typing import List, Dict, Set
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models.task import Task, TaskType, TaskStatus
from app.db.models.index_log import IndexLog
from app.crud import album as album_crud
from app.core.config_manager import config_manager

from app.service.tasks import thumbnail, metadata, scan, face, ocr

DEFAULT_PRIORITIES = {
    TaskType.SCAN_FOLDER: 10,
    TaskType.PROCESS_BASIC: 9,
    TaskType.GENERATE_THUMBNAIL: 8,
    TaskType.EXTRACT_METADATA: 5,
    TaskType.REBUILD_METADATA: 5,
    TaskType.REBUILD_THUMBNAILS: 4,
    TaskType.RECOGNIZE_FACE: 1,
    TaskType.CLASSIFY_IMAGE: 1,
    TaskType.OCR: 1,
}

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
        
        # Category Management
        self.paused_categories: Set[str] = set()
        self.category_map = {
            TaskType.SCAN_FOLDER: 'scanning',
            TaskType.PROCESS_BASIC: 'scanning',
            TaskType.PROCESS_IMAGE: 'scanning', # Legacy
            TaskType.GENERATE_THUMBNAIL: 'scanning',
            
            TaskType.EXTRACT_METADATA: 'metadata',
            TaskType.REBUILD_METADATA: 'metadata',
            
            TaskType.RECOGNIZE_FACE: 'face',
            TaskType.CLASSIFY_IMAGE: 'face', # or 'ai'
            TaskType.OCR: 'ocr',
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
        self._recover_unfinished_tasks()
        
        # Use config for max_workers
        max_workers = config_manager.config.task.max_concurrent_tasks
        self.process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)
        
        self.worker_task = asyncio.create_task(self.worker_loop())
        self.result_task = asyncio.create_task(self.result_loop())
        logging.info(f"TaskManager started with {max_workers} workers")

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

    def get_grouped_status(self, db: Session):
        """Get task counts grouped by category"""
        stats = []
        # Define categories to show
        categories = ['scanning', 'metadata', 'face', 'ocr']
        
        # Priority map for categories (higher is better)
        cat_priority = {
            'scanning': 10,
            'metadata': 5,
            'face': 1,
            'ocr': 1
        }

        for cat in categories:
            # Find types belonging to this category
            types = [t for t, c in self.category_map.items() if c == cat]
            pending = db.query(Task).filter(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.PROCESSING]),
                Task.type.in_(types)
            ).count()
            
            # Completed is always 0 as we delete them
            completed = 0
            
            failed = db.query(Task).filter(
                Task.status == TaskStatus.FAILED,
                Task.type.in_(types)
            ).count()

            stats.append({
                'category': cat,
                'pending': pending,
                'completed': completed,
                'failed': failed,
                'status': 'paused' if cat in self.paused_categories else 'active',
                'priority': cat_priority.get(cat, 0)
            })
            
        # Sort by priority desc
        stats.sort(key=lambda x: x['priority'], reverse=True)
        return stats

    def pause_category(self, category: str):
        self.paused_categories.add(category)
        logging.info(f"Paused task category: {category}")

    def resume_category(self, category: str):
        if category in self.paused_categories:
            self.paused_categories.remove(category)
            logging.info(f"Resumed task category: {category}")

    def add_task(self, db: Session, type: str, payload: dict, priority: int = 0):
        if priority == 0:
            priority = DEFAULT_PRIORITIES.get(type, 0)
            
        task = Task(type=type, payload=payload, priority=priority)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def add_tasks(self, db: Session, tasks_data: List[Dict]):
        """Batch add tasks"""
        if not tasks_data:
            return
        
        tasks = []
        for t_data in tasks_data:
            priority = t_data.get('priority', 0)
            if priority == 0:
                priority = DEFAULT_PRIORITIES.get(t_data['type'], 0)
            
            tasks.append(Task(
                type=t_data['type'],
                payload=t_data.get('payload', {}),
                priority=priority,
                status=TaskStatus.PENDING
            ))
            
        db.bulk_save_objects(tasks)
        db.commit()
        # No refresh for bulk
        
        # Update stats locally if needed, or let worker update
        self.scan_status['total_files'] += len(tasks)

    async def worker_loop(self):
        logging.info("TaskManager worker loop started")
        active_tasks = set()
        idle_start_time = None
        
        while self.running:
            try:
                # Clean up finished tasks
                active_tasks = {t for t in active_tasks if not t.done()}
                # Update status
                if active_tasks:
                    self.scan_status['running'] = True
                    idle_start_time = None
                
                # Manage Pool Lifecycle (Resource Release)
                if not active_tasks:
                    if idle_start_time is None:
                        idle_start_time = datetime.now()
                    elif (datetime.now() - idle_start_time).total_seconds() > 30:
                        # Idle for 30s, shutdown pool to release resources
                        if self.process_pool:
                            logging.info("TaskManager idle for 30s, shutting down process pool to release resources")
                            self.process_pool.shutdown(wait=False)
                            self.process_pool = None
                else:
                    # Ensure pool exists
                    if self.process_pool is None:
                        max_workers = config_manager.config.task.max_concurrent_tasks
                        logging.info(f"Restarting process pool with {max_workers} workers")
                        self.process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)

                # Limit concurrency (double check against pool size if needed, but here we limit async tasks)
                # We should match max_concurrent_tasks
                max_concurrency = config_manager.config.task.max_concurrent_tasks
                if len(active_tasks) >= max_concurrency:
                    await asyncio.sleep(0.1)
                    continue

                db = SessionLocal()
                try:
                    # Determine paused types
                    paused_types = []
                    for type_enum, cat in self.category_map.items():
                        if cat in self.paused_categories:
                            paused_types.append(type_enum)

                    # Poll for tasks
                    query = db.query(Task).filter(Task.status == TaskStatus.PENDING)
                    
                    if paused_types:
                        query = query.filter(Task.type.notin_(paused_types))
                        
                    task = query.order_by(Task.priority.desc(), Task.created_at.asc()).first()
                    
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

    def _recover_unfinished_tasks(self):
        """启动时恢复未完成的任务：重置PROCESSING为PENDING，统计未完成任务数"""
        db = SessionLocal()
        try:
            # 1. 统计未完成任务（PENDING + PROCESSING）
            pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
            processing_tasks = db.query(Task).filter(Task.status == TaskStatus.PROCESSING).count()
            total_unfinished = pending_tasks + processing_tasks

            if total_unfinished == 0:
                logging.info("No unfinished tasks to recover")
                return

            # 2. 重置PROCESSING任务为PENDING（服务重启后，PROCESSING的任务已中断）
            if processing_tasks > 0:
                # 获取所有PROCESSING状态的任务
                processing_task_list = db.query(Task).filter(Task.status == TaskStatus.PROCESSING).all()
                for task in processing_task_list:
                    # 检查payload中是否包含force=True
                    if task.payload and task.payload.get('force') is True:
                        # 如果是强制任务，重置时移除force标记，避免无限循环重复处理
                        new_payload = task.payload.copy()
                        new_payload['force'] = False
                        task.payload = new_payload
                        logging.info(f"Reset task {task.id} payload: removed force=True")
                    
                    task.status = TaskStatus.PENDING
                
                db.commit()
                logging.info(f"Reset {processing_tasks} PROCESSING tasks to PENDING (recovered)")

            # 3. 初始化扫描状态（标记有未完成任务，更新统计）
            self.scan_status['running'] = True
            self.scan_status['message'] = f"Recovered {total_unfinished} unfinished tasks"
            self.scan_status['total_files'] = max(self.scan_status['total_files'], total_unfinished)
            logging.info(f"Recovered total {total_unfinished} unfinished tasks (pending: {pending_tasks}, processing: {processing_tasks})")

        except Exception as e:
            logging.error(f"Failed to recover unfinished tasks: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    def _flush_results(self, items: List[Dict]):
        db = SessionLocal()
        try:
            # 1. Prepare batch photo inserts
            photos_to_create = []
            index_logs = []
            
            # Map of temp photo_id to file_path for task chaining
            processed_photos = {} # photo_id -> file_path

            for item in items:
                task_type = item['task_type']
                status = item['status']
                
                # Handle PROCESS_BASIC (and legacy PROCESS_IMAGE if needed)
                if status == TaskStatus.COMPLETED and (task_type == TaskType.PROCESS_BASIC or task_type == TaskType.PROCESS_IMAGE):
                    res = item['result']
                    if 'photo_create_data' in res:
                        data = res['photo_create_data']
                        photos_to_create.append(data)
                        index_logs.append(IndexLog(action='added', file_path=data['file_path'], photo_id=data['photo_id']))
                        
                        # Store for chaining
                        processed_photos[str(data['photo_id'])] = data['file_path']

                        # Update stats
                        self.scan_status['added'] += 1
                        self.scan_status['processed_files'] += 1

            # Batch insert photos
            if photos_to_create:
                album_crud.batch_create_photos(db, photos_to_create)
                db.add_all(index_logs)
                
                # Now chain subsequent tasks for newly created photos
                for photo_id, file_path in processed_photos.items():
                    # 1. Metadata Task (High Priority)
                    db.add(Task(
                        type=TaskType.EXTRACT_METADATA,
                        payload={'file_path': file_path, 'photo_id': photo_id},
                        priority=5,
                        status=TaskStatus.PENDING
                    ))
                    # 2. Face Recognition Task (Low Priority)
                    db.add(Task(
                        type=TaskType.RECOGNIZE_FACE,
                        payload={'file_path': file_path, 'photo_id': photo_id},
                        priority=1,
                        status=TaskStatus.PENDING
                    ))
                    # 3. OCR Task (Low Priority)
                    db.add(Task(
                        type=TaskType.OCR,
                        payload={'file_path': file_path, 'photo_id': photo_id},
                        priority=1,
                        status=TaskStatus.PENDING
                    ))

            # 2. Update tasks
            for item in items:
                task = db.query(Task).filter(Task.id == item['task_id']).first()
                if not task:
                    continue
                
                if item['status'] == TaskStatus.COMPLETED:
                    # Delete completed task to prevent table bloat
                    db.delete(task)
                    # self.scan_status['processed_files'] += 1 # Already updated in loop or logic? 
                    # Actually processed_files is updated in item processing for PROCESS_BASIC
                    # For other tasks, we should update it here?
                    # The scan_status['processed_files'] is a global counter for the current "Session" or "Batch".
                    # Let's keep it incrementing.
                    
                else:
                    task.status = item['status']
                    task.error = item.get('error')
                    task.result = item.get('result')
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
            return await scan.handle_scan_folder(self, task, db)
        elif task.type == TaskType.PROCESS_IMAGE:
            return await scan.handle_process_image(self, task, db)
        elif task.type == TaskType.PROCESS_BASIC:
            return await scan.handle_process_basic(self, task, db)
        elif task.type == TaskType.GENERATE_THUMBNAIL:
            return await thumbnail.handle_generate_thumbnail(self, task, db)
        elif task.type == TaskType.REBUILD_THUMBNAILS:
            return await thumbnail.handle_rebuild_thumbnails(self, task, db)
        elif task.type == TaskType.REBUILD_METADATA:
            return await metadata.handle_rebuild_metadata(self, task, db)
        elif task.type == TaskType.EXTRACT_METADATA:
            return await metadata.handle_extract_metadata(self, task, db)
        elif task.type == TaskType.RECOGNIZE_FACE:
            return await face.handle_face_recognition(self, task, db)
        elif task.type == TaskType.OCR:
            return await ocr.handle_ocr_task(self, task, db)
        else:
            return {'status': 'not_implemented', 'type': task.type}
