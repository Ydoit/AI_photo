#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/18 20:56
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-api.py
@Description : 
"""
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from datetime import date


from schemas import (
    StationRead, StationCreate, TrainRead, TrainCreate,
    TrainScheduleRead, TrainWithScheduleRead, TrainTypeDictRead,
    SeatTypeDictRead, TrainScheduleCreate
)
from crud import (
    create_station, get_station, get_stations, get_stations_by_province_city,
    create_train, get_train_by_no_date, get_trains_by_departure_arrival,
    create_train_schedule, get_train_schedules_by_no_date,
    get_train_schedules, update_station, get_train_by_code_date
)
from railway.db.models.models import Train
from railway.dependencies import get_db

# 初始化 FastAPI 应用
app = FastAPI(title="12306 车次信息 API", description="基于 FastAPI+PostgreSQL+SQLAlchemy 的铁路车次信息管理接口", version="1.0.0")


# ------------------------------ 车站接口 ------------------------------
@app.post("/stations", response_model=StationRead, summary="创建/更新车站（存在则检查更新）")
def create_or_update_station_api(station: StationCreate, db: Session = Depends(get_db)):
    # 1. 根据车站名称查询是否已存在
    db_station = get_station(db, station.station_name)

    if db_station:
        # 2. 存在时，对比信息是否有更新（排除create_time，只对比业务字段）
        # 提取StationCreate的所有业务字段（排除不需要对比的字段）
        update_fields = [
            "station_pinyin", "station_py", "province", "city",
            "district", "telecode", "is_high_speed", "status"
        ]
        # 检查每个字段是否有变化
        has_update = False
        for field in update_fields:
            db_value = getattr(db_station, field, None)
            new_value = getattr(station, field, None)
            # 处理None值对比（避免None == "" 的误判）
            if (db_value is None and new_value is not None) or (db_value is not None and new_value is None):
                has_update = True
                break
            if db_value != new_value:
                has_update = True
                break

        if has_update:
            # 3. 有更新则执行更新操作
            updated_station = update_station(db, db_station, station)
            # 自定义响应头，标识操作类型（可选）
            headers = {"X-Operation-Type": "update"}
            return updated_station
        else:
            # 4. 无更新则返回原数据，提示无变化
            headers = {"X-Operation-Type": "no_change"}
            return db_station

    # 5. 不存在则创建新车站
    new_station = create_station(db, station)
    headers = {"X-Operation-Type": "create"}
    return new_station

@app.get("/stations/{station_name}", response_model=StationRead, summary="根据ID获取车站")
def get_station_api(station_name: str, db: Session = Depends(get_db)):
    db_station = get_station(db, station_name)
    if not db_station:
        raise HTTPException(status_code=404, detail="车站不存在")
    return db_station

@app.get("/stations", response_model=List[StationRead], summary="获取车站列表（分页）")
def get_stations_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_stations(db, skip, limit)

@app.get("/stations/province-city", response_model=List[StationRead], summary="根据省市获取车站")
def get_stations_by_province_city_api(province: str, city: str, db: Session = Depends(get_db)):
    return get_stations_by_province_city(db, province, city)

# ------------------------------ 车次接口 ------------------------------
@app.post("/trains", response_model=TrainRead, summary="创建车次")
def create_train_api(train: TrainCreate, db: Session = Depends(get_db)):
    db_train = get_train_by_code_date(db, train.train_code, train.train_date)
    if db_train:
        raise HTTPException(status_code=400, detail="该日期的车次已存在")
    # 验证出发站和到达站是否存在
    if not get_station(db, train.from_station):
        raise HTTPException(status_code=404, detail="出发站不存在")
    if not get_station(db, train.to_station):
        raise HTTPException(status_code=404, detail="到达站不存在")
    # 3. 创建车次
    create_train(db, train)
    # 4. 重新查询（带关联信息预加载），用于响应返回
    new_db_train = get_train_by_code_date(db, train.train_code, train.train_date)
    return new_db_train  # 返回带关联车站信息的车次对象

@app.get("/trains/{train_code}/{train_date}", response_model=TrainRead, summary="根据车次+日期获取车次信息")
def get_train_api(
        train_code: str = Path(..., description="车次号（例如：G2025）"),
        train_date: date = Path(..., description="开行日期（格式：YYYY-MM-DD，例如：2025-11-19）"),
        db: Session = Depends(get_db)):
    db_train = get_train_by_code_date(db, train_code, train_date)
    if not db_train:
        raise HTTPException(status_code=404, detail="车次不存在")
    return db_train

@app.get("/trains", response_model=List[TrainRead], summary="查询出发站→到达站的车次")
def get_trains_api(
    departure_station_id: str,
    arrival_station_id: str,
    train_date: date,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return get_trains_by_departure_arrival(db, departure_station_id, arrival_station_id, train_date, skip, limit)

# ------------------------------ 时刻表接口 ------------------------------
@app.post("/train-schedules", response_model=TrainScheduleRead, summary="创建车次时刻表")
def create_train_schedule_api(schedule: TrainScheduleCreate, db: Session = Depends(get_db)):
    # 验证车次和车站是否存在
    if not db.query(Train).filter(Train.train_no == schedule.train_no).first():
        raise HTTPException(status_code=404, detail="车次不存在")
    if not get_station(db, schedule.station_name):
        raise HTTPException(status_code=404, detail="车站不存在")
    return create_train_schedule(db, schedule)

@app.get("/train-schedules/{train_no}/{train_date}", response_model=List[TrainScheduleRead], summary="根据车次+日期获取时刻表")
def get_train_schedules_api(train_no: str, train_date: date, db: Session = Depends(get_db)):
    schedules = get_train_schedules_by_no_date(db, train_no, train_date)
    if not schedules:
        raise HTTPException(status_code=404, detail="时刻表不存在")
    return schedules

@app.get("/trains/with-schedule/{train_no}/{train_date}", response_model=TrainWithScheduleRead, summary="获取车次+时刻表完整信息")
def get_train_with_schedule_api(
        train_no: str = Path(..., description="车次唯一编号（例如：620000K5020U）"),
        train_date: date = Path(..., description="开行日期（格式：YYYY-MM-DD，例如：2025-11-19）"),
        db: Session = Depends(get_db)):
    train = get_train_by_no_date(db, train_no, train_date)
    if not train:
        raise HTTPException(status_code=404, detail="车次不存在")
    schedules = get_train_schedules(db, train.train_id)
    return TrainWithScheduleRead(**train.__dict__, schedules=schedules)

if __name__ == "__main__":
    import uvicorn
    # 运行服务：http://127.0.0.1:8005/docs 可访问 Swagger 文档
    uvicorn.run("api:app", host="0.0.0.0", port=8005, reload=True)
