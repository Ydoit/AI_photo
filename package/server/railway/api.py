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

from fastapi import FastAPI, Depends, HTTPException
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
    get_all_train_types, get_all_seat_types, get_train_schedules
)
from railway.db.models.models import Train
from railway.dependencies import get_db

# 初始化 FastAPI 应用
app = FastAPI(title="12306 车次信息 API", description="基于 FastAPI+PostgreSQL+SQLAlchemy 的铁路车次信息管理接口", version="1.0.0")


# ------------------------------ 车站接口 ------------------------------
@app.post("/stations", response_model=StationRead, summary="创建车站")
def create_station_api(station: StationCreate, db: Session = Depends(get_db)):
    db_station = get_station(db, station.station_id)
    if db_station:
        raise HTTPException(status_code=400, detail="车站编码已存在")
    return create_station(db, station)

@app.get("/stations/{station_id}", response_model=StationRead, summary="根据ID获取车站")
def get_station_api(station_id: str, db: Session = Depends(get_db)):
    db_station = get_station(db, station_id)
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
    db_train = get_train_by_no_date(db, train.train_no, train.train_date)
    if db_train:
        raise HTTPException(status_code=400, detail="该日期的车次已存在")
    # 验证出发站和到达站是否存在
    if not get_station(db, train.departure_station_id):
        raise HTTPException(status_code=404, detail="出发站不存在")
    if not get_station(db, train.arrival_station_id):
        raise HTTPException(status_code=404, detail="到达站不存在")
    return create_train(db, train)

@app.get("/trains/{train_no}/{train_date}", response_model=TrainRead, summary="根据车次+日期获取车次信息")
def get_train_api(train_no: str, train_date: date, db: Session = Depends(get_db)):
    db_train = get_train_by_no_date(db, train_no, train_date)
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
    if not db.query(Train).filter(Train.train_id == schedule.train_id).first():
        raise HTTPException(status_code=404, detail="车次不存在")
    if not get_station(db, schedule.station_id):
        raise HTTPException(status_code=404, detail="车站不存在")
    return create_train_schedule(db, schedule)

@app.get("/train-schedules/{train_no}/{train_date}", response_model=List[TrainScheduleRead], summary="根据车次+日期获取时刻表")
def get_train_schedules_api(train_no: str, train_date: date, db: Session = Depends(get_db)):
    schedules = get_train_schedules_by_no_date(db, train_no, train_date)
    if not schedules:
        raise HTTPException(status_code=404, detail="时刻表不存在")
    return schedules

@app.get("/trains/with-schedule/{train_no}/{train_date}", response_model=TrainWithScheduleRead, summary="获取车次+时刻表完整信息")
def get_train_with_schedule_api(train_no: str, train_date: date, db: Session = Depends(get_db)):
    train = get_train_by_no_date(db, train_no, train_date)
    if not train:
        raise HTTPException(status_code=404, detail="车次不存在")
    schedules = get_train_schedules(db, train.train_id)
    return TrainWithScheduleRead(**train.__dict__, schedules=schedules)

# ------------------------------ 字典表接口 ------------------------------
@app.get("/train-types", response_model=List[TrainTypeDictRead], summary="获取所有列车类型")
def get_train_types_api(db: Session = Depends(get_db)):
    return get_all_train_types(db)

@app.get("/seat-types", response_model=List[SeatTypeDictRead], summary="获取所有席位类型")
def get_seat_types_api(db: Session = Depends(get_db)):
    return get_all_seat_types(db)

if __name__ == "__main__":
    import uvicorn
    # 运行服务：http://127.0.0.1:8000/docs 可访问 Swagger 文档
    uvicorn.run("api:app", host="0.0.0.0", port=8005, reload=True)
