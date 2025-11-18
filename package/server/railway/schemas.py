#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/18 20:50
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-schemas.py
@Description : 
"""

from datetime import date, time, datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

# ------------------------------ 基础模型 ------------------------------
class BaseSchema(BaseModel):
    """基础 Schema，包含公共字段"""
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True  # 支持从 ORM 模型直接转换

# ------------------------------ 车站相关 ------------------------------
class StationCreate(BaseModel):
    station_id: str = Field(min_length=6, max_length=6, description="车站6位编码")
    station_name: str = Field(description="车站名称")
    station_pinyin: str = Field(description="拼音（全拼|首字母，如beijingxi|bjx）")
    province: str = Field(description="所属省份")
    city: str = Field(description="所属城市")
    district: Optional[str] = Field(None, description="所属区县")
    telecode: Optional[str] = Field(None, max_length=3, description="电报码")
    is_high_speed: int = Field(ge=0, le=1, default=0, description="是否高铁站（0=普速，1=高铁）")
    status: int = Field(ge=0, le=1, default=1, description="状态（1=运营，0=暂停）")

class StationRead(BaseSchema):
    station_id: str
    station_name: str
    station_pinyin: str
    province: str
    city: str
    district: Optional[str]
    telecode: Optional[str]
    is_high_speed: int
    status: int

# ------------------------------ 列车类型字典 ------------------------------
class TrainTypeDictRead(BaseModel):
    type_code: str
    type_name: str
    description: Optional[str]

    class Config:
        from_attributes = True

# ------------------------------ 席位类型字典 ------------------------------
class SeatTypeDictRead(BaseModel):
    seat_code: str
    seat_name: str
    seat_level: int

    class Config:
        from_attributes = True

# ------------------------------ 车次相关 ------------------------------
class TrainCreate(BaseModel):
    train_no: str = Field(description="车次编号（G123/D456）")
    train_type: str = Field(max_length=2, description="列车类型编码（G/D/Z等）")
    departure_station_id: str = Field(min_length=6, max_length=6, description="出发站编码")
    arrival_station_id: str = Field(min_length=6, max_length=6, description="到达站编码")
    train_date: date = Field(description="开行日期（2024-10-01）")
    departure_time: time = Field(description="发车时间（08:00:00）")
    arrival_time: time = Field(description="终到时间（14:30:00）")
    total_duration: int = Field(ge=0, description="全程时长（分钟）")
    total_mileage: float = Field(ge=0, description="全程里程（公里）")
    is_canceled: int = Field(ge=0, le=1, default=0, description="是否停运（0=正常）")
    is_odd_even: Optional[int] = Field(0, ge=0, le=4, description="开行规律（0=每日）")

class TrainRead(BaseSchema):
    train_id: int
    train_no: str
    train_type: str
    train_type_info: Optional[TrainTypeDictRead]  # 关联列车类型信息
    departure_station_id: str
    departure_station: StationRead  # 关联出发站信息
    arrival_station_id: str
    arrival_station: StationRead  # 关联到达站信息
    train_date: date
    departure_time: time
    arrival_time: time
    total_duration: int
    total_mileage: float
    is_canceled: int
    is_odd_even: Optional[int]

# ------------------------------ 时刻表相关 ------------------------------
class TrainScheduleCreate(BaseModel):
    train_id: int = Field(description="关联车次ID")
    station_id: str = Field(min_length=6, max_length=6, description="途经站编码")
    sequence: int = Field(ge=1, description="途经顺序（1=出发站）")
    arrival_time: Optional[time] = Field(None, description="到站时间（出发站为NULL）")
    departure_time: Optional[time] = Field(None, description="发车时间（到达站为NULL）")
    stop_duration: int = Field(ge=0, default=0, description="停留时长（分钟）")
    accumulated_mileage: float = Field(ge=0, description="累计里程（公里）")
    is_departure: int = Field(ge=0, le=1, default=0, description="是否出发站（1=是）")
    is_arrival: int = Field(ge=0, le=1, default=0, description="是否到达站（1=是）")
    platform: Optional[str] = Field(None, description="停靠站台")
    seat_remain: Optional[Dict[str, int]] = Field(None, description="席位余票")

class TrainScheduleRead(BaseSchema):
    schedule_id: int
    train_id: int
    station_id: str
    station: StationRead  # 关联车站信息
    sequence: int
    arrival_time: Optional[time]
    departure_time: Optional[time]
    stop_duration: int
    accumulated_mileage: float
    is_departure: int
    is_arrival: int
    platform: Optional[str]
    seat_remain: Optional[Dict[str, int]]

# ------------------------------ 组合响应模型 ------------------------------
class TrainWithScheduleRead(TrainRead):
    """包含时刻表的车次信息"""
    schedules: List[TrainScheduleRead] = Field(description="途经站点时刻表")