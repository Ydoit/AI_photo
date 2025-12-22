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
    """任务详情返回模型"""
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
        from_attributes = True


class TaskCreate(BaseModel):
    """创建任务请求体"""
    type: str
    payload: Optional[Dict[str, Any]] = {}


@router.get("/", response_model=List[TaskSchema], summary="获取任务列表")
def list_tasks(
    status: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    分页查询任务列表，可按状态过滤。
    默认按创建时间倒序返回前 50 条。
    """
    query = db.query(Task).order_by(Task.created_at.desc())
    if status:
        query = query.filter(Task.status == status)
    return query.limit(limit).all()


@router.get("/stats", summary="获取任务统计")
def get_task_stats(db: Session = Depends(get_db)):
    """
    返回当前系统中 PROCESS_IMAGE 类型且状态为 FAILED 的任务数量。
    """
    failed_count = db.query(Task).filter(
        Task.type == TaskType.PROCESS_IMAGE,
        Task.status == TaskStatus.FAILED
    ).count()
    return {"failed_process_tasks": failed_count}


@router.get("/grouped-status", summary="按状态分组统计任务")
def get_grouped_status(db: Session = Depends(get_db)):
    """
    调用 TaskManager 获取按状态分组的任务统计信息。
    """
    return TaskManager.get_instance().get_grouped_status(db)


@router.post("/categories/{category}/pause", summary="暂停指定分类任务")
def pause_category(category: str):
    """
    暂停某一分类（category）下的所有待处理任务。
    """
    TaskManager.get_instance().pause_category(category)
    return {"status": "success"}


@router.post("/categories/{category}/resume", summary="恢复指定分类任务")
def resume_category(category: str):
    """
    恢复之前被暂停的某一分类（category）下的任务。
    """
    TaskManager.get_instance().resume_category(category)
    return {"status": "success"}


@router.get("/{task_id}", response_model=TaskSchema, summary="根据 ID 获取任务详情")
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    """
    根据任务 UUID 返回任务详情；若任务不存在则返回 404。
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/", response_model=TaskSchema, summary="创建新任务")
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    """
    创建一个新任务。
    - type：任务类型，需为系统支持的 TaskType 枚举值。
    - payload：可选，任务附加数据。
    若 type 非法则返回 400。
    """
    # Validate type
    try:
        task_type = TaskType(task_in.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid task type: {task_in.type}")

    task = TaskManager.get_instance().add_task(db, task_in.type, task_in.payload)
    return task


@router.post("/{task_id}/cancel", response_model=TaskSchema, summary="取消任务")
def cancel_task(task_id: UUID, db: Session = Depends(get_db)):
    """
    将指定任务状态置为 CANCELLED。
    仅允许取消处于待处理或运行中的任务；已完成、已失败或已取消的任务将返回 400。
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Task is already finished")

    task.status = TaskStatus.CANCELLED
    db.commit()
    db.refresh(task)
    return task
