import asyncio
import logging
import concurrent.futures
from typing import List, Dict
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models.task import Task, TaskType, TaskStatus
from app.db.models.index_log import IndexLog
from app.crud import album as album_crud

from app.service.tasks import thumbnail, metadata, scan

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
            return await scan.handle_scan_folder(self, task, db)
        elif task.type == TaskType.PROCESS_IMAGE:
            return await scan.handle_process_image(self, task, db)
        elif task.type == TaskType.REBUILD_THUMBNAILS:
            return await thumbnail.handle_rebuild_thumbnails(self, task, db)
        elif task.type == TaskType.REBUILD_METADATA:
            return await metadata.handle_rebuild_metadata(self, task, db)
        else:
            return {'status': 'not_implemented', 'type': task.type}
