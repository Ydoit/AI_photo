#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/8/10 22:26 
@Author      : SiYuan 
@Email       : siyuan044@gmail.com
@File        : TrailSnap-media.py 
@Description : 
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Enum, JSON, CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from app.db.base import Base

# 枚举类型定义
MediaType = Enum('image', 'video', 'live', name='media_type')  # 媒体类型：图片、视频、实况图

class Media(Base):
    """
    媒体文件表（图片、视频、实况图）
    存储用户拍摄的照片、视频等基础信息以及元数据
    """
    __tablename__ = 'media'
    id = Column(Integer, primary_key=True)                 # 主键
    file_path = Column(String, nullable=False)             # 文件在存储系统中的路径
    media_type = Column(MediaType, nullable=False)         # 媒体类型（image/video/live）
    captured_at = Column(DateTime)                         # 拍摄时间
    md5 = Column(CHAR(32), unique=True, nullable=False, index=True)  # 32位HEX，固定长度
    description = Column(Text)                             # 媒体描述/标题
    latitude = Column(Float)                               # 拍摄位置纬度
    longitude = Column(Float)                              # 拍摄位置经度
    city_id = Column(Integer, ForeignKey('cities.id'))     # 所属城市ID
    exif_data = Column(JSON)                                # JSON格式的扩展元数据（如EXIF信息）

    # 关系
    persons = relationship('Person', secondary='person_media', back_populates='media_items')
    city = relationship('City', back_populates='media_items')
    scenic_spots = relationship('ScenicSpot', secondary='scenic_spot_media', back_populates='photos')
    ticket = relationship('Ticket', uselist=False, back_populates='media')
    trips = relationship('Trip', secondary='trip_media', back_populates='media_items')
    albums = relationship('Album', secondary='album_media', back_populates='media_items')


if __name__ == '__main__':
    pass
