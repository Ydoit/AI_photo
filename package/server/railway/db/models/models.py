#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/18 20:51
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-models.py
@Description : 
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, SmallInteger, DECIMAL, Date, Time,
    JSON, ForeignKey, Index, UniqueConstraint, DateTime
)
from sqlalchemy.orm import relationship
from railway.db.base import Base

class Station(Base):
    """全国车站基础表"""
    __tablename__ = "station"

    # station_name = Column(String(length=6), primary_key=True, comment="车站唯一6位编码")
    station_name = Column(String(length=50), primary_key=True, nullable=False, comment="车站名称")
    station_pinyin = Column(String(length=100), nullable=False, comment="车站拼音（全拼）")
    station_py = Column(String(length=10), nullable=False, comment="车站拼音（首字母简拼）")
    province = Column(String(length=30), nullable=True, comment="所属省份/直辖市")
    city = Column(String(length=30), nullable=False, comment="所属城市")
    district = Column(String(length=30), nullable=True, comment="所属区县")
    telecode = Column(String(length=3), nullable=True, comment="车站电报码")
    is_high_speed = Column(SmallInteger, nullable=False, default=0, comment="是否高铁站（0=普速，1=高铁）")
    status = Column(SmallInteger, nullable=False, default=1, comment="状态（1=运营，0=暂停）")
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 索引/约束
    __table_args__ = (
        UniqueConstraint("station_name", name="uk_station_name"),  # 车站名称唯一
        Index("idx_station_pinyin", "station_pinyin"),  # 拼音搜索索引
        Index("idx_province_city", "province", "city"),  # 省市筛选索引
    )

    # 关联关系：车站作为出发站的车次
    departure_trains = relationship("Train", foreign_keys="Train.from_station", back_populates="departure_station")
    # 关联关系：车站作为到达站的车次
    arrival_trains = relationship("Train", foreign_keys="Train.to_station", back_populates="arrival_station")
    # 关联关系：车站的途经时刻表
    schedules = relationship("TrainSchedule", back_populates="station")

class TrainTypeDict(Base):
    """列车类型字典表"""
    __tablename__ = "train_type_dict"

    type_code = Column(String(length=2), primary_key=True, comment="类型编码（G/D/Z/T/K/C）")
    type_name = Column(String(length=20), nullable=False, comment="类型名称（高铁/动车等）")
    description = Column(String(length=100), nullable=True, comment="类型说明（最高时速等）")

    # 关联关系：该类型的所有车次
    trains = relationship("Train", back_populates="train_type_info")

class SeatTypeDict(Base):
    """席位类型字典表"""
    __tablename__ = "seat_type_dict"

    seat_code = Column(String(length=10), primary_key=True, comment="席位编码（YZ/EDZ等）")
    seat_name = Column(String(length=20), nullable=False, comment="席位名称（硬座/二等座等）")
    seat_level = Column(SmallInteger, nullable=False, default=1, comment="席位等级（1=普通，4=商务）")

class Train(Base):
    """车次基础信息表"""
    __tablename__ = "train"

    train_id = Column(
        Integer,
        autoincrement=True,primary_key=True, comment="车次记录唯一ID"
    )
    train_no = Column(String(length=20), nullable=False, comment="车次唯一编号")
    train_code = Column(String(length=20), nullable=False, comment="车次（G123/D456）")
    train_type = Column(String(length=2), ForeignKey("train_type_dict.type_code", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, comment="列车类型（关联train_type_dict.type_code）")
    from_station = Column(String(length=6), ForeignKey("station.station_name", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, comment="出发站")
    to_station = Column(String(length=6), ForeignKey("station.station_name", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, comment="到达站")
    train_date = Column(Date, nullable=False, comment="开行日期（2024-10-01）")
    departure_time = Column(Time, nullable=False, comment="出发站发车时间（08:00:00）")
    arrival_time = Column(Time, nullable=False, comment="到达站终到时间（14:30:00）")
    total_duration = Column(Integer, nullable=False, comment="全程时长（分钟）")
    total_mileage = Column(DECIMAL(10, 1), nullable=False, comment="全程里程（公里）")
    is_canceled = Column(SmallInteger, nullable=False, default=0, comment="是否停运（0=正常，1=停运）")
    is_odd_even = Column(SmallInteger, nullable=True, default=0, comment="开行规律（0=每日，1=单日等）")
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 索引/约束
    __table_args__ = (
        UniqueConstraint("train_no", "train_date", name="uk_train_no_date"),  # 车次+日期唯一
        Index("idx_departure_arrival", "from_station", "to_station"),  # 出发-到达站索引
        Index("idx_train_date", "train_date"),  # 日期筛选索引
        Index("idx_train_type", "train_type"),  # 类型筛选索引
    )

    # 关联关系
    departure_station = relationship("Station", foreign_keys=[from_station], back_populates="departure_trains")
    arrival_station = relationship("Station", foreign_keys=[to_station], back_populates="arrival_trains")
    train_type_info = relationship("TrainTypeDict", back_populates="trains")
    schedules = relationship("TrainSchedule", back_populates="train", cascade="all, delete-orphan")  # 删除车次时级联删除时刻表

class TrainSchedule(Base):
    """车次途经站点时刻表"""
    __tablename__ = "train_schedule"

    schedule_id = Column(
        Integer,autoincrement=True,
        primary_key=True, comment="时刻表记录唯一ID"
    )
    train_id = Column(Integer, ForeignKey("train.train_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, comment="关联车次ID")
    station_name = Column(String(length=6), ForeignKey("station.station_name", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, comment="途经站编码")
    sequence = Column(SmallInteger, nullable=False, comment="途经顺序（1=出发站）")
    arrival_time = Column(Time, nullable=True, comment="到站时间（出发站为NULL）")
    departure_time = Column(Time, nullable=True, comment="发车时间（到达站为NULL）")
    stop_duration = Column(SmallInteger, nullable=False, default=0, comment="停留时长（分钟）")
    accumulated_mileage = Column(DECIMAL(10, 1), nullable=False, comment="累计里程（公里）")
    is_departure = Column(SmallInteger, nullable=False, default=0, comment="是否出发站（1=是）")
    is_arrival = Column(SmallInteger, nullable=False, default=0, comment="是否到达站（1=是）")
    platform = Column(String(length=10), nullable=True, comment="停靠站台（3号站台）")
    seat_remain = Column(JSON, nullable=True, comment="席位余票（{\"硬座\":100,\"二等座\":20}）")
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 索引/约束
    __table_args__ = (
        UniqueConstraint("train_id", "station_name", name="uk_train_station"),  # 车次+站点唯一
        UniqueConstraint("train_id", "sequence", name="uk_train_sequence"),  # 车次+顺序唯一
        Index("idx_train_id", "train_id"),  # 车次查询索引
        Index("idx_station_name", "station_name"),  # 站点筛选索引
    )

    # 关联关系
    train = relationship("Train", back_populates="schedules")
    station = relationship("Station", back_populates="schedules")
