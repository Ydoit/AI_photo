from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.db.models.task import Task
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

router = APIRouter()

class TaskSchema(BaseModel):
    id: UUID
    type: str
    status: str
    priority: int
    created_at: datetime
    updated_at: Optional[datetime]
    error: Optional[str]
    
    class Config:
        orm_mode = True

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
