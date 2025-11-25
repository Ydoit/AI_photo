#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/9 23:44 
@Author      : SiYuan 
@Email       : siyuan044@qq.com 
@File        : TrailSnap-location.py 
@Description : 
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Country(Base):
    """
    国家表
    存储国家信息
    """
    __tablename__ = 'countries'
    id = Column(Integer, primary_key=True)                 # 主键
    name = Column(String, nullable=False)                  # 国家名称
    country_code = Column(String, nullable=False)          # 国家编码

    provinces = relationship('Province', back_populates='country')

class Province(Base):
    """
    省份/州信息表
    """
    __tablename__ = 'provinces'
    id = Column(Integer, primary_key=True)                 # 主键
    name = Column(String, nullable=False)                  # 省份名称
    country_id = Column(Integer, ForeignKey('countries.id')) # 所属国家
    province_code = Column(String, nullable=False)          # 省份编码

    country = relationship('Country', back_populates='provinces')
    cities = relationship('City', back_populates='province')

class City(Base):
    """
    城市信息表
    存储城市及其与省份的关系
    """
    __tablename__ = 'cities'
    id = Column(Integer, primary_key=True)                 # 主键
    name = Column(String, nullable=False)                  # 城市名称
    province_id = Column(Integer, ForeignKey('provinces.id')) # 所属省份
    city_code = Column(String, nullable=False)  # 城市编码

    province = relationship('Province', back_populates='cities')
    media_items = relationship('Media', back_populates='city')
    scenic_spots = relationship('ScenicSpot', back_populates='city')
    tickets_origin = relationship('Ticket', back_populates='origin_city', foreign_keys='Ticket.origin_city_id')
    tickets_dest = relationship('Ticket', back_populates='destination_city', foreign_keys='Ticket.dest_city_id')
