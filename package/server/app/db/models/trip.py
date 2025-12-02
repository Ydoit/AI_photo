#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/9 23:44 
@Author      : SiYuan 
@Email       : siyuan044@qq.com 
@File        : TrailSnap-trip.py 
@Description : 
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum, Numeric, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base import Base

TicketType = Enum('train', 'flight', 'bus', name='ticket_type')  # 票据类型：火车票、飞机票、汽车票

class Ticket(Base):
    """
    票据信息表
    存储火车票、机票、汽车票等识别结果
    """
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True)                 # 主键
    ticket_type = Column(TicketType, nullable=False)       # 票据类型
    origin_city_id = Column(Integer, ForeignKey('cities.id')) # 出发城市
    dest_city_id = Column(Integer, ForeignKey('cities.id'))   # 到达城市
    depart_time = Column(DateTime)                         # 出发时间
    arrive_time = Column(DateTime)                         # 到达时间
    media_id = Column(Integer, ForeignKey('media.id'))     # 票据图片对应的媒体
    origin_city = relationship('City', back_populates='tickets_origin', foreign_keys=[origin_city_id])
    destination_city = relationship('City', back_populates='tickets_dest', foreign_keys=[dest_city_id])
    media = relationship('Media', back_populates='ticket')
    trips = relationship('Trip', secondary='trip_ticket', back_populates='tickets')

class Trip(Base):
    """
    旅行行程表
    存储一次旅行的时间范围、描述及关联的媒体和票据
    """
    __tablename__ = 'trips'
    id = Column(Integer, primary_key=True)                 # 主键
    name = Column(String)                                  # 行程名称
    start_date = Column(DateTime)                          # 行程开始时间
    end_date = Column(DateTime)                            # 行程结束时间
    description = Column(Text)                             # 行程描述
    media_items = relationship('Media', secondary='trip_media', back_populates='trips')
    tickets = relationship('Ticket', secondary='trip_ticket', back_populates='trips')

class TripMedia(Base):
    """
    旅行-媒体关联表
    用于将行程与多张照片关联，并保存顺序
    """
    __tablename__ = 'trip_media'
    trip_id = Column(Integer, ForeignKey('trips.id'), primary_key=True)  # 行程ID
    media_id = Column(Integer, ForeignKey('media.id'), primary_key=True) # 媒体ID
    sequence = Column(Integer)                                           # 媒体在行程中的顺序

class TripTicket(Base):
    """
    旅行-票据关联表
    用于将行程与多张票据关联
    """
    __tablename__ = 'trip_ticket'
    trip_id = Column(Integer, ForeignKey('trips.id'), primary_key=True)  # 行程ID
    ticket_id = Column(Integer, ForeignKey('tickets.id'), primary_key=True) # 票据ID

class TrainTicket(Base):
    """火车票模型"""
    __tablename__ = "train_tickets"

    # 修改为UUID类型主键
    id = Column(
        String(36),
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),  # 自动生成UUID
        comment="票据ID（UUID）"
    )
    train_code = Column(String(20), index=True, nullable=False, comment="车次号（如G1920）")
    departure_station = Column(String(50), nullable=False, comment="出发站")
    arrival_station = Column(String(50), nullable=False, comment="到达站")
    date_time = Column(DateTime, nullable=False, comment="发车时间")
    carriage = Column(String(10), nullable=False, comment="车厢号（如8A、12）")
    seat_num = Column(String(10), nullable=False, comment="座位号（如12F、05下）")
    berth_type = Column(String(10), default="无", comment="铺位类型（上/中/下/无）")
    price = Column(Numeric(10, 2), nullable=False, comment="票价（保留两位小数）")
    seat_type = Column(String(20), nullable=False, comment="座位类型（一等座/二等座/商务座等）")
    name = Column(String(50), nullable=False, comment="乘车人姓名")
    discount_type = Column(String(20), default="全价票", comment="优惠类型（学生票/儿童票/优惠票/全价票等）")
    total_mileage = Column(DECIMAL(10, 1), nullable=False, default=0, comment="线路里程（公里）")
    total_running_time = Column(Integer, nullable=False, default=0, comment="累计运行时间（分钟）")
    stop_stations = Column(Text, nullable=True, default="[]", comment="经停站列表，JSON格式存储")
    comments = Column(Text, nullable=True, comment="备注信息")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")