#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/23 23:14
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-train_ticket.py
@Description : 
"""
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from app.crud.train_ticket import create_train_ticket, get_train_ticket, update_train_ticket, delete_train_ticket
from app.db.models.trip import TrainTicket
from app.schemas.train_ticket import TrainTicketResponse, TrainTicketCreate, TrainTicketListResponse, TrainTicketUpdate
from app.schemas.user import UserCreate, UserRead
from app.crud.user import create_user
from app.dependencies import get_db

router = APIRouter()

# ------------------- 火车票接口 -------------------

@router.post("", response_model=TrainTicketResponse, summary="创建火车票记录")
def create_ticket(
        ticket: TrainTicketCreate,
        db: Session = Depends(get_db)
):
    """
    创建新的火车票记录

    - **train_code**: 车次号（如G1920）
    - **departure_station**: 出发站
    - **arrival_station**: 到达站
    - **datetime**: 发车时间（格式：YYYY-MM-DD HH:MM:SS）
    - **carriage**: 车厢号（如8A、12）
    - **seat_num**: 座位号（如12F、05下）
    - **berth_type**: 铺位类型（上/中/下/无，默认为空）
    - **price**: 票价（保留两位小数）
    - **seat_type**: 座位类型（一等座/二等座/商务座等）
    - **name**: 乘车人姓名
    - **discount_type**: 优惠类型（学生票/儿童票/优惠票/全价票，默认全价票）
    - **total_running_time**: 总运行时间（分钟，可选）
    - **total_mileage**: 总里程（公里，可选）
    - **stop_stations**: 途经站点列表（可选）
    """
    return create_train_ticket(db=db, ticket=ticket)


@router.get("/{ticket_id}", response_model=TrainTicketResponse, summary="获取单张火车票")
def read_ticket(
        ticket_id: int = Path(..., ge=1, description="火车票ID"),
        db: Session = Depends(get_db)
):
    """根据ID获取单张火车票的详细信息"""
    db_ticket = get_train_ticket(db=db, ticket_id=ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="火车票记录不存在")
    return db_ticket


@router.get("", response_model=TrainTicketListResponse, summary="获取火车票列表")
def read_tickets(
        db: Session = Depends(get_db),
        skip: int = Query(0, ge=0, description="跳过的记录数"),
        limit: int = Query(10, ge=1, le=100, description="每页最大记录数"),
        train_code: Optional[str] = Query(None, description="按车次号模糊查询"),
        name: Optional[str] = Query(None, description="按乘车人姓名模糊查询"),
        departure_station: Optional[str] = Query(None, description="按出发站模糊查询"),
        arrival_station: Optional[str] = Query(None, description="按到达站模糊查询"),
        start_datetime: Optional[datetime] = Query(None, description="发车时间起始（格式：YYYY-MM-DD HH:MM:SS）"),
        end_datetime: Optional[datetime] = Query(None, description="发车时间结束（格式：YYYY-MM-DD HH:MM:SS）")
):
    """
    获取火车票列表（支持多条件过滤和分页）

    - 支持按车次号、乘车人、出发站、到达站模糊查询
    - 支持按发车时间范围查询
    - 支持分页（skip：跳过条数，limit：每页条数）
    """
    # 构建过滤条件
    filters: Dict[str, Any] = {
        "train_code": train_code,
        "name": name,
        "departure_station": departure_station,
        "arrival_station": arrival_station
    }

    # 处理时间范围过滤
    query = db.query(TrainTicket)
    if start_datetime:
        query = query.filter(TrainTicket.datetime >= start_datetime)
    if end_datetime:
        query = query.filter(TrainTicket.datetime <= end_datetime)

    # 应用其他过滤条件
    for key, value in filters.items():
        if value is not None:
            query = query.filter(getattr(TrainTicket, key).ilike(f"%{value}%"))

    # 计算总记录数和分页数据
    query = query.order_by(TrainTicket.date_time.desc())  # 按发车时间倒序（最新的在前）

    # 3. 最后分页（offset + limit）
    total = query.count()  # 计算总记录数（排序前的总条数，不受分页影响）
    items = query.offset(skip).limit(limit).all()  # 先排序，再分页

    return {"total": total, "items": items}


@router.put("/{ticket_id}", response_model=TrainTicketResponse, summary="更新火车票记录")
def update_ticket(
        ticket_update: TrainTicketUpdate,
        ticket_id: int = Path(..., ge=1, description="火车票ID"),
        db: Session = Depends(get_db)
):
    """根据ID更新火车票信息（只需要提供要更新的字段）"""
    db_ticket = update_train_ticket(db=db, ticket_id=ticket_id, ticket_update=ticket_update)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="火车票记录不存在")
    return db_ticket


@router.delete("/{ticket_id}", response_model=dict, summary="删除火车票记录")
def delete_ticket(
        ticket_id: int = Path(..., ge=1, description="火车票ID"),
        db: Session = Depends(get_db)
):
    """根据ID删除火车票记录"""
    success = delete_train_ticket(db=db, ticket_id=ticket_id)
    if not success:
        raise HTTPException(status_code=404, detail="火车票记录不存在")
    return {"message": "火车票记录删除成功"}

