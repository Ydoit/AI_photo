#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/18 20:50
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-crud.py
@Description : 
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from railway.db.models.models import Station, Train, TrainSchedule
from schemas import (
    StationCreate, TrainCreate, TrainScheduleCreate
)

# ------------------------------ 车站 CRUD ------------------------------
def create_station(db: Session, station: StationCreate) -> Station:
    """创建车站"""
    db_station = Station(**station.model_dump())
    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    return db_station

def update_station(db: Session, db_station: Station, update_data: StationCreate) -> Station:
    """更新车站信息（仅更新有变化的字段）"""
    # 遍历 StationCreate 的所有字段，只更新有变化的值
    update_dict = update_data.model_dump(exclude_unset=True)  # 排除未传递的字段
    for field, value in update_dict.items():
        if field in ["station_name", "create_time"]:  # 不允许修改车站名称和创建时间
            continue
        setattr(db_station, field, value)

    db.commit()
    db.refresh(db_station)
    return db_station

def get_station(db: Session, station_name: str) -> Optional[Station]:
    """根据ID获取车站"""
    return db.query(Station).filter(Station.station_name == station_name).first()

def get_stations(db: Session, skip: int = 0, limit: int = 100) -> List[Station]:
    """获取车站列表（分页）"""
    return db.query(Station).offset(skip).limit(limit).all()

def get_stations_by_province_city(db: Session, province: str, city: str) -> List[Station]:
    """根据省市获取车站"""
    return db.query(Station).filter(Station.province == province, Station.city == city).all()

# ------------------------------ 车次 CRUD ------------------------------
def create_train(db: Session, train: TrainCreate) -> Train:
    """创建车次"""
    db_train = Train(**train.model_dump())
    db.add(db_train)
    db.commit()
    db.refresh(db_train)
    return db_train

def get_train_by_no_date(db: Session, train_no: str, train_date: date) -> Optional[Train]:
    """根据车次编号+日期获取车次（含关联信息）"""
    return db.query(Train).filter(
        Train.train_no == train_no,
        Train.train_date == train_date
    ).options(
        joinedload(Train.departure_station),
        joinedload(Train.arrival_station),
        joinedload(Train.train_type_info)
    ).first()

def get_train_by_code_date(db: Session, train_code: str, train_date: date) -> Optional[Train]:
    """根据车次编号+日期获取车次（含关联信息）"""
    return db.query(Train).filter(
        Train.train_code == train_code,
        Train.train_date == train_date
    ).options(
        joinedload(Train.departure_station),
        joinedload(Train.arrival_station)
    ).first()

def get_trains_by_departure_arrival(db: Session, from_station: str, to_station: str, train_date: date, skip: int = 0, limit: int = 50) -> List[Train]:
    """根据出发站+到达站+日期查询车次"""
    return db.query(Train).filter(
        Train.from_station == from_station,
        Train.to_station == to_station,
        Train.train_date == train_date,
        Train.is_canceled == 0
    ).options(
        joinedload(Train.from_station),
        joinedload(Train.to_station)
    ).offset(skip).limit(limit).order_by(Train.departure_time).all()

# ------------------------------ 时刻表 CRUD ------------------------------
def create_train_schedule(db: Session, schedule: TrainScheduleCreate) -> TrainSchedule:
    """创建车次时刻表"""
    db_schedule = TrainSchedule(**schedule.model_dump())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def get_train_schedules(db: Session, train_no: str) -> List[TrainSchedule]:
    """根据车次ID获取时刻表（按顺序排序）"""
    return db.query(TrainSchedule).filter(
        TrainSchedule.train_no == train_no
    ).options(
        joinedload(TrainSchedule.station)
    ).order_by(TrainSchedule.sequence).all()

def get_train_schedules_by_no_date(db: Session, train_code: str, train_date: date) -> Optional[List[TrainSchedule]]:
    """根据车次编号+日期获取时刻表"""
    train = get_train_by_no_date(db, train_code, train_date)
    if not train:
        return None
    return get_train_schedules(db, train.train_no)
