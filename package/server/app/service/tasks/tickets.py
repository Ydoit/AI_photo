import logging
import os
import aiohttp
from aiohttp import FormData
from sqlalchemy.orm import Session
from app.db.models.task import Task, TaskType
from app.db.models.photo import Photo, FileType
from app.db.models.trip import TrainTicket
from typing import Dict, Any, List
from datetime import datetime
from app.core.config_manager import config_manager
from app.service import storage
import re

logger = logging.getLogger(__name__)

async def handle_ticket_task(task_manager, task: Task, db: Session) -> Dict[str, Any]:
    try:
        force = task.payload.get('force', False)

        if task.payload and 'photo_id' in task.payload:
            photo_id = task.payload['photo_id']
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                return {'status': 'skipped', 'reason': 'photo not found'}

            if not force:
                tasks_status = photo.processed_tasks or {}
                if tasks_status.get('tickets'):
                     return {'status': 'skipped', 'reason': 'already processed'}

            return await process_single_photo(task_manager, photo, db)

        # Generator Mode
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
                    if not tasks_status.get('tickets'):
                        should_process = True
                if should_process:
                    tasks_to_create.append({
                        'type': TaskType.RECOGNIZE_TICKET,
                        'payload': {'photo_id': str(p.id), 'force': force},
                        'priority': 2
                    })

            if tasks_to_create:
                task_manager.add_tasks(db, tasks_to_create)
                generated_count += len(tasks_to_create)

            offset += batch_size

        return {
            'processed': 0,
            'generated_tasks': generated_count,
            'message': f'Generated {generated_count} ticket recognition tasks'
        }

    except Exception as e:
        logger.error(f"Ticket task failed: {e}")
        raise e

async def process_single_photo(task_manager, photo: Photo, db: Session) -> Dict[str, Any]:
    try:
        target_path = storage.get_preview_path(photo.id, db)
        if not os.path.exists(target_path):
            target_path = photo.file_path
            if not target_path or not os.path.exists(target_path):
                return {'status': 'failed', 'error': 'file not found'}

        async with aiohttp.ClientSession() as session:
            with open(target_path, 'rb') as f:
                file_data = f.read()

            form_data = FormData()
            form_data.add_field(
                name='file',
                value=file_data,
                filename=photo.filename,
                content_type='image/jpeg'
            )

            api_url = f"{config_manager.config.ai.ai_api_url}/tickets/predict"
            async with session.post(api_url, data=form_data) as response:
                if response.status == 200:
                    result = await response.json()
                    # === Auto-add tickets to database ===
                    if result and 'tickets' in result:
                        tickets_data = result['tickets']
                        added_count = 0
                        for t_info in tickets_data:
                            try:
                                # Validation
                                if not t_info.get('train_code') or not t_info.get('datetime'):
                                    continue
                                # Parse datetime
                                dt_str = t_info.get('datetime')
                                dt = None
                                # Try standard formats
                                formats = [
                                    "%Y年%m月%d日 %H:%M",
                                    "%Y年%m月%d日%H:%M",
                                    "%Y-%m-%d %H:%M",
                                    "%Y/%m/%d %H:%M"
                                ]
                                for fmt in formats:
                                    try:
                                        dt = datetime.strptime(dt_str, fmt)
                                        break
                                    except ValueError:
                                        continue
                                if not dt:
                                    logger.warning(f"Skipping ticket due to invalid datetime: {dt_str}")
                                    continue

                                # Parse Price
                                price_val = 0.0
                                price_str = str(t_info.get('price', '0')).replace('元', '').replace('￥', '').strip()
                                try:
                                    price_val = float(price_str)
                                except:
                                    pass

                                # Check duplicate
                                existing = db.query(TrainTicket).filter(
                                    TrainTicket.train_code == t_info['train_code'],
                                    TrainTicket.date_time == dt,
                                    TrainTicket.seat_num == (t_info.get('seat_num') or '无座')
                                ).first()
                                if existing:
                                    logger.info(f"Duplicate ticket found: {t_info['train_code']} {dt}")
                                    continue

                                # Create Ticket
                                new_ticket = TrainTicket(
                                    train_code=t_info['train_code'],
                                    departure_station=t_info.get('departure_station', '未知'),
                                    arrival_station=t_info.get('arrival_station', '未知'),
                                    date_time=dt,
                                    carriage=t_info.get('carriage') or '无',
                                    seat_num=t_info.get('seat_num') or '无座',
                                    berth_type=t_info.get('berth_type') or '无',
                                    price=price_val,
                                    seat_type=t_info.get('seat_type') or '二等座',
                                    name=t_info.get('name') or '未知',
                                    discount_type=t_info.get('discount_type') or '全价票',
                                    total_mileage=0,
                                    total_running_time=0,
                                    stop_stations="[]",
                                    comments=f"自动识别自图片: {photo.filename}"
                                )
                                db.add(new_ticket)
                                db.flush()
                                t_info['saved_id'] = new_ticket.id
                                added_count += 1

                            except Exception as ex:
                                logger.error(f"Error saving ticket to DB: {ex}")
                        if added_count > 0:
                            logger.info(f"Successfully added {added_count} tickets from photo {photo.id}")

                    # Update processed status
                    tasks_status = photo.processed_tasks or {}
                    tasks_status['tickets'] = True
                    photo.processed_tasks = tasks_status
                    db.add(photo)
                    db.commit()
                    return result
                else:
                    text = await response.text()
                    logger.error(f"AI Service error: {response.status} {text}")
                    raise Exception(f"AI Service error: {response.status}")

    except Exception as e:
        logger.error(f"Process ticket failed: {e}")
        raise e

def release_resources():
    pass
