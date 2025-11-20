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

class Train(Base):
    """车次基础信息表（固定不变的属性）"""
    __tablename__ = "train"

    train_id = Column(
        Integer, autoincrement=True,
        primary_key=True, comment="ID"
    )

    train_no = Column(String(length=20), nullable=False, comment="铁路内部唯一编号（如0G12300）")
    train_code = Column(String(length=20), nullable=False, comment="对外公布车次（G123/D456）")
    train_type = Column(String(length=2), nullable=False, comment="列车类型（G/D/Z/T/K等）")
    from_station = Column(String(length=50), ForeignKey("station.station_name", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, comment="固定出发站")
    to_station = Column(String(length=50), ForeignKey("station.station_name", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, comment="固定到达站")

    create_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 索引/约束（车次对外唯一）
    __table_args__ = (
        # UniqueConstraint("train_no", name="uk_train_no"),
        Index("idx_train_no", "train_no"),  # 车次查询核心索引
        Index("idx_train_code", "train_code"),  # 车次查询核心索引
        Index("idx_from_to_station", "from_station", "to_station"),  # 出发-到达站筛选
    )

    # -------------------------- 关键补充：缺失的关联属性 --------------------------
    # 1. 对应 Station.departure_trains 的反向关联（出发站）
    # 必须指定 foreign_keys=from_station，因为 Train 有两个外键关联 Station，避免歧义
    departure_station = relationship(
        "Station",
        foreign_keys=[from_station],  # 明确关联当前模型的 from_station 外键
        back_populates="departure_trains",  # 和 Station 里的 departure_trains 对应
    )
    # 2. 对应 Station.arrival_trains 的反向关联（到达站）
    arrival_station = relationship(
        "Station",
        foreign_keys=[to_station],  # 明确关联当前模型的 to_station 外键
        back_populates="arrival_trains",  # 和 Station 里的 arrival_trains 对应
    )
    # -----------------------------------------------------------------------------

    # 关联关系：一个车次对应多个运行计划版本
    # operation_plans = relationship("TrainOperationPlan", back_populates="train", cascade="all, delete-orphan")

class TrainOperationPlan(Base):
    """车次运行计划（时刻表版本表）- 每次调整新增版本，保留历史"""
    __tablename__ = "train_operation_plan"

    operation_id = Column(
        Integer, autoincrement=True,
        primary_key=True, comment="运行计划唯一ID（版本标识）"
    )
    train_no = Column(String(length=20), nullable=False, comment="关联车次唯一编号") # 去掉外键依赖 ForeignKey("train.train_no", ondelete="RESTRICT", onupdate="CASCADE")
    plan_version = Column(String(length=10), nullable=False, comment="版本号（如V1/20251120V1，便于识别调整）")
    start_date = Column(Date, nullable=False, comment="计划生效开始日期（含）")
    end_date = Column(Date, nullable=True, comment="计划生效结束日期（含），NULL表示永久有效")
    run_rule = Column(SmallInteger, nullable=False, default=0, comment="开行规律：0=每日，1=工作日，2=周末，3=单日，4=双日，5=自定义")
    custom_run_days = Column(JSON, nullable=True, comment="自定义开行日期（run_rule=5时用，如[\"2025-11-20\",\"2025-11-22\"]）")
    station_num = Column(SmallInteger, nullable=False, default=2, comment="该版本途经车站数（含起止站）")
    total_mileage = Column(DECIMAL(10, 1), nullable=False, default=0, comment="该版本全程里程（公里）")
    total_running_time = Column(Time, nullable=False, comment="该版本全程运行时间（如05:56）")
    is_canceled = Column(SmallInteger, nullable=False, default=0, comment="该版本是否停运：0=正常，1=停运")
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 索引/约束（确保版本唯一、查询高效）
    __table_args__ = (
        # 同一车次的版本号唯一
        UniqueConstraint("train_no", "plan_version", name="uk_train_version"),
        # 核心查询索引：车次+生效时间范围（快速匹配某天的有效计划）
        Index("idx_train_effective_date", "train_no", "start_date", "end_date"),
        # 辅助筛选索引
        Index("idx_run_rule", "run_rule"),
        Index("idx_is_canceled", "is_canceled"),
    )

    # 关联关系
    # train = relationship("Train", back_populates="operation_plans")
    # 一个运行计划对应一套时刻表，删除计划时级联删除时刻表
    schedules = relationship("TrainSchedule", back_populates="operation_plan", cascade="all, delete-orphan")

class TrainSchedule(Base):
    """车次途经站点时刻表（关联具体运行计划版本）"""
    __tablename__ = "train_schedule"

    schedule_id = Column(
        Integer, autoincrement=True,
        primary_key=True, comment="时刻表记录唯一ID"
    )
    operation_id = Column(Integer, ForeignKey("train_operation_plan.operation_id", ondelete="CASCADE", onupdate="CASCADE"),
                          nullable=False, comment="关联运行计划ID（核心关联）")
    train_code = Column(String(length=20), nullable=False, comment="对外公布车次（G123/D456）")
    station_name = Column(String(length=50), ForeignKey("station.station_name", ondelete="RESTRICT", onupdate="CASCADE"),
                          nullable=False, comment="途经站")
    sequence = Column(SmallInteger, nullable=False, comment="途经顺序（1=出发站，递增）")
    arrive_day_diff = Column(SmallInteger, nullable=False, comment="到达时间距发车的天数差（如跨天为1）")
    arrival_time = Column(Time, nullable=True, comment="到站时间（出发站为NULL）")
    departure_time = Column(Time, nullable=True, comment="发车时间（到达站为NULL）")
    stop_duration = Column(SmallInteger, nullable=False, default=0, comment="停留时长（分钟）")
    accumulated_mileage = Column(DECIMAL(10, 1), nullable=False, comment="累计里程（公里）")
    running_time = Column(Time, nullable=False, comment="累计运行时间（如05:56）")
    is_departure = Column(SmallInteger, nullable=False, default=0, comment="是否出发站：1=是")
    is_arrival = Column(SmallInteger, nullable=False, default=0, comment="是否到达站：1=是")
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 索引/约束（确保版本内的站点唯一、顺序唯一）
    __table_args__ = (
        UniqueConstraint("operation_id", "station_name", name="uk_operation_station"),
        UniqueConstraint("operation_id", "sequence", name="uk_operation_sequence"),
        # 核心查询索引：运行计划ID+顺序（快速获取排序后的时刻表）
        Index("idx_operation_sequence", "operation_id", "sequence"),
        Index("idx_station_name", "station_name"),
    )

    # 关联关系
    operation_plan = relationship("TrainOperationPlan", back_populates="schedules")
    station = relationship("Station", back_populates="schedules")
