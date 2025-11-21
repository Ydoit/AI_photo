#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/18 20:56
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-api.py
@Description : 
"""
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Path, Body, Query
from sqlalchemy.orm import Session
from datetime import date


from schemas import (
    StationRead, StationCreate, TrainRead, TrainCreate,
    TrainScheduleRead, TrainScheduleCreate, BaseResponse, StationSingleQuery, StationListQuery, StationListResponse
)
from railway.crud import (
    create_station,
    create_train,
    create_train_schedule,
    get_train_schedules, update_station, get_station_single, get_station_list,
)
from railway.db.models.models import Train
from railway.db.dependencies import get_db

# 初始化 FastAPI 应用
app = FastAPI(title="12306 车次信息 API", description="基于 FastAPI+PostgreSQL+SQLAlchemy 的铁路车次信息管理接口", version="1.0.0")


# ------------------------------ 车站接口 ------------------------------
@app.post(
    "/stations",
    response_model=BaseResponse[StationRead],  # 统一响应模型+业务数据结构
    summary="创建/更新车站（存在则检查更新）"
)
def create_or_update_station_api(
        station: StationCreate = Body(..., description="车站信息"),
        db: Session = Depends(get_db)
):
    # 调用 CRUD 函数，获取 code、msg、data
    code, msg, data = create_station(db, station)

    # 返回统一响应格式
    return BaseResponse(
        code=code,
        msg=msg,
        data=data  # data 为 ORM 模型，BaseResponse 会通过 from_attributes 自动转换为 StationRead
    )

# ------------------------------ 单条车站查询接口 ------------------------------
@app.get(
    "/stations/single",
    response_model=BaseResponse[StationRead],
    summary="单条车站查询（ID/电报码/名称三选一）"
)
def query_station_single(
    # 查询参数（与StationSingleQuery对应，使用Query绑定）
    station_id: Optional[int] = Query(None, description="车站ID（与telecode/name三选一）"),
    telecode: Optional[str] = Query(None, max_length=3, description="车站电报码（唯一，三选一）"),
    station_name: Optional[str] = Query(None, description="车站名称（精确匹配，三选一）"),
    db: Session = Depends(get_db)
):
    # 构造查询参数对象
    query = StationSingleQuery(
        station_id=station_id,
        telecode=telecode,
        station_name=station_name
    )
    # 调用CRUD函数
    code, msg, data = get_station_single(db, query)
    # 返回统一响应
    return BaseResponse(code=code, msg=msg, data=data)

# ------------------------------ 车站列表查询接口 ------------------------------
@app.get(
    "/stations",
    response_model=BaseResponse[StationListResponse],  # data为分页字典
    summary="车站列表查询（支持筛选、模糊搜索、分页）"
)
def query_station_list(
    # 筛选参数
    province: Optional[str] = Query(None, description="所属省份（精确匹配）"),
    city: Optional[str] = Query(None, description="所属城市（精确匹配）"),
    district: Optional[str] = Query(None, description="所属区县（精确匹配）"),
    is_high_speed: Optional[int] = Query(None, ge=0, le=1, description="是否高铁站（0=普速，1=高铁）"),
    status: Optional[int] = Query(1, ge=0, le=1, description="状态（1=运营，0=暂停）"),
    # 搜索参数
    keyword: Optional[str] = Query(None, description="搜索关键词（匹配名称/全拼/简拼）"),
    # 分页参数
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数（1-100）"),
    db: Session = Depends(get_db)
):
    # 构造查询参数对象
    query = StationListQuery(
        province=province,
        city=city,
        district=district,
        is_high_speed=is_high_speed,
        status=status,
        keyword=keyword,
        page=page,
        page_size=page_size
    )
    # 调用CRUD函数
    code, msg, data = get_station_list(db, query)
    # 返回统一响应
    return BaseResponse(code=code, msg=msg, data=data)


if __name__ == "__main__":
    import uvicorn
    # 运行服务：http://127.0.0.1:8005/docs 可访问 Swagger 文档
    uvicorn.run("api:app", host="0.0.0.0", port=8005, reload=True)
