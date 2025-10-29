#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/8/10 22:31 
@Author      : SiYuan 
@Email       : siyuan044@gmail.com
@File        : backend-scenic.py 
@Description : 
"""
from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, Float, String
from sqlalchemy.orm import relationship

from app.db.base import Base

class ScenicSpot(Base):
    """
    景区信息表
    存储旅游景点数据
    """
    __tablename__ = 'scenic_spots'
    id = Column(Integer, primary_key=True)                 # 主键
    name = Column(String, nullable=False)                  # 景区名称
    city_id = Column(Integer, ForeignKey('cities.id'))     # 所属城市
    latitude = Column(Float)                               # 景区纬度
    longitude = Column(Float)                              # 景区经度
    description = Column(Text)                             # 景区描述
    city = relationship('City', back_populates='scenic_spots')
    photos = relationship('Media', secondary='scenic_spot_media', back_populates='scenic_spots')

class ScenicSpotMedia(Base):
    """
    景区-媒体关联表
    用于将景区与其相关照片关联
    """
    __tablename__ = 'scenic_spot_media'
    scenic_id = Column(Integer, ForeignKey('scenic_spots.id'), primary_key=True) # 景区ID
    media_id = Column(Integer, ForeignKey('media.id'), primary_key=True)         # 媒体ID


if __name__ == '__main__':
    pass
