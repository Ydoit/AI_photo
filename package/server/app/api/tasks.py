from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.db.models.task import Task, TaskStatus, TaskType
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from app.service.task_manager import TaskManager

router = APIRouter()

class TaskSchema(BaseModel):
    id: UUID
    type: str
    status: str
    priority: int
    created_at: datetime
    updated_at: Optional[datetime]
    error: Optional[str]
    payload: Optional[Dict[str, Any]]
    total_items: Optional[int]
    processed_items: Optional[int]
    
    class Config:
        orm_mode = True

class TaskCreate(BaseModel):
    type: str
    payload: Optional[Dict[str, Any]] = {}

@router.get("/", response_model=List[TaskSchema])
def list_tasks(status: str = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(Task).order_by(Task.created_at.desc())
    if status:
        query = query.filter(Task.status == status)
    return query.limit(limit).all()

@router.get("/{task_id}", response_model=TaskSchema)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/", response_model=TaskSchema)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    # Validate type
    try:
        task_type = TaskType(task_in.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid task type: {task_in.type}")
        
    task = TaskManager.get_instance().add_task(db, task_in.type, task_in.payload)
    return task

@router.post("/{task_id}/cancel", response_model=TaskSchema)
def cancel_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Task is already finished")
        
    task.status = TaskStatus.CANCELLED
    db.commit()
    db.refresh(task)
    return task
