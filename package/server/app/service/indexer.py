from sqlalchemy.orm import Session
from app.db.models.task import TaskType
from app.service.task_manager import TaskManager

# Keep status for compatibility, but it will be updated by TaskManager via polling or we just return "Running"
status = {
    'running': False,
    'progress': 0.0,
    'added': 0,
    'deleted': 0,
    'errors': 0,
    'message': 'Idle'
}

def rebuild_index(db: Session):
    if status['running']:
        return

    # Submit task
    TaskManager.get_instance().add_task(db, TaskType.SCAN_FOLDER, {}, priority=10)

    # Update status to indicate start
    status['running'] = True
    status['progress'] = 0.0
    status['message'] = "Async scan task submitted"
