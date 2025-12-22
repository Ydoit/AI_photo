#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/23 23:14
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-train_ticket.py
@Description : 
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query, UploadFile, File, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
import csv
import json
import io

from app.crud.train_ticket import (
    create_train_ticket, 
    get_train_ticket, 
    update_train_ticket, 
    delete_train_ticket,
    get_all_train_tickets
)
from app.db.models.trip import TrainTicket
from app.schemas.train_ticket import TrainTicketResponse, TrainTicketCreate, TrainTicketListResponse, TrainTicketUpdate
from app.dependencies import get_db

router = APIRouter()

# ------------------- 火车票接口 -------------------

@router.post("/import", summary="导入车票数据")
async def import_tickets(
    file: UploadFile = File(..., description="数据文件（支持JSON/CSV）"),
    db: Session = Depends(get_db)
):
    """
    导入车票数据（支持JSON和CSV格式）
    
    - **文件限制**: 最大10MB
    - **重复处理**: 根据ID更新现有记录，不存在则创建
    - **格式要求**: 
        - CSV需包含表头
        - JSON需为对象数组
    """
    # 1. 验证文件大小
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="文件大小超过10MB限制")
    
    # 2. 确定文件格式
    content_type = file.content_type
    filename = file.filename.lower()
    
    data_list = []
    
    try:
        if "json" in content_type or filename.endswith(".json"):
            data_list = json.loads(contents.decode("utf-8"))
            if not isinstance(data_list, list):
                raise HTTPException(status_code=400, detail="JSON文件格式错误：应为对象数组")
                
        elif "csv" in content_type or filename.endswith(".csv"):
            # 处理BOM
            decoded = contents.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(decoded))
            data_list = [row for row in reader]
            
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式：仅支持JSON和CSV")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的JSON文件")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码错误，请使用UTF-8编码")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    # 3. 处理数据导入
    success_count = 0
    failed_count = 0
    updated_count = 0
    created_count = 0
    errors = []

    for idx, item in enumerate(data_list):
        try:
            # 尝试获取ID
            ticket_id = item.get("id")
            
            # 数据清洗：移除空值
            item = {k: v for k, v in item.items() if v is not None and v != ""}
            
            # 特殊处理：stop_stations 如果是字符串形式的JSON，可能需要保持原样
            # TrainTicketCreate defined stop_stations as Optional[str]
            
            # 验证并转换数据
            # 使用Pydantic模型进行验证和类型转换
            try:
                # 这里使用TrainTicketUpdate来验证，因为它允许字段缺失（CSV可能缺列）
                # 但对于创建，我们需要TrainTicketCreate的必填项
                # 策略：如果ID存在且DB存在，用Update；否则用Create
                
                db_ticket = None
                if ticket_id:
                    db_ticket = get_train_ticket(db, ticket_id)
                
                if db_ticket:
                    # 更新模式
                    ticket_update = TrainTicketUpdate(**item)
                    update_data = ticket_update.model_dump(exclude_unset=True)
                    
                    for key, value in update_data.items():
                        setattr(db_ticket, key, value)
                    
                    updated_count += 1
                else:
                    # 创建模式
                    # 如果是CSV导入，可能会缺少ID字段（如果是新数据）
                    # 如果item中有id但DB无，则是恢复数据/指定ID创建
                    
                    # 验证必填字段
                    ticket_create = TrainTicketCreate(**item)
                    model_data = ticket_create.model_dump()
                    
                    # 如果原数据有ID，强制使用该ID
                    if ticket_id:
                        model_data["id"] = ticket_id
                        
                    # 处理默认值
                    if "stop_stations" not in model_data or not model_data["stop_stations"]:
                        model_data["stop_stations"] = "[]"
                        
                    new_ticket = TrainTicket(**model_data)
                    db.add(new_ticket)
                    created_count += 1
                
                # 提交事务
                db.commit()
                success_count += 1
                
            except Exception as e:
                db.rollback()
                raise e
                
        except Exception as e:
            failed_count += 1
            errors.append(f"第 {idx + 1} 行处理失败: {str(e)}")
            # 继续处理下一条

    return {
        "message": "导入完成",
        "total": len(data_list),
        "success": success_count,
        "failed": failed_count,
        "details": {
            "created": created_count,
            "updated": updated_count
        },
        "errors": errors[:10]  # 仅返回前10个错误以免响应过大
    }


@router.get("/export", summary="导出车票数据")
def export_tickets(
    format: str = Query("json", description="导出格式：json 或 csv"),
    db: Session = Depends(get_db)
):
    """
    导出所有车票数据
    
    - **format**: 指定导出格式 (json/csv)
    - 返回相应格式的文件下载
    """
    tickets = get_all_train_tickets(db)
    
    if format.lower() == "json":
        # 转换为JSON兼容格式
        data = jsonable_encoder(tickets)
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=train_tickets.json"}
        )
        
    elif format.lower() == "csv":
        if not tickets:
            # 空CSV
            return Response(
                content="",
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=train_tickets.csv"}
            )
            
        # 获取字段名（使用Pydantic模型的字段或ORM模型的字段）
        # 这里使用ORM模型的__table__.columns.keys()能获取所有数据库字段
        # 但为了更好的格式，我们可以手动指定顺序或使用Schema
        
        fieldnames = [
            "id", "train_code", "departure_station", "arrival_station", "date_time",
            "carriage", "seat_num", "berth_type", "price", "seat_type", "name",
            "discount_type", "total_running_time", "total_mileage", "stop_stations", 
            "comments", "created_at"
        ]
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for ticket in tickets:
            row = {}
            for field in fieldnames:
                val = getattr(ticket, field, None)
                # 处理特殊类型
                if isinstance(val, datetime):
                    val = val.strftime("%Y-%m-%d %H:%M:%S")
                row[field] = val
            writer.writerow(row)
            
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=train_tickets.csv"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="不支持的导出格式，请使用 json 或 csv")


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
    - **comments**: 车票备注（可选）
    """
    return create_train_ticket(db=db, ticket=ticket)


@router.get("/{ticket_id}", response_model=TrainTicketResponse, summary="获取单张火车票")
def read_ticket(
        ticket_id: str = Path(..., description="火车票ID"),
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
        ticket_id: str = Path(..., description="火车票ID"),
        db: Session = Depends(get_db)
):
    """根据ID更新火车票信息（只需要提供要更新的字段）"""
    db_ticket = update_train_ticket(db=db, ticket_id=ticket_id, ticket_update=ticket_update)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="火车票记录不存在")
    return db_ticket


@router.delete("/{ticket_id}", response_model=dict, summary="删除火车票记录")
def delete_ticket(
        ticket_id: str = Path(..., description="火车票ID"),
        db: Session = Depends(get_db)
):
    """根据ID删除火车票记录"""
    success = delete_train_ticket(db=db, ticket_id=ticket_id)
    if not success:
        raise HTTPException(status_code=404, detail="火车票记录不存在")
    return {"message": "火车票记录删除成功"}

