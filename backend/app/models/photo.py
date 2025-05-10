#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/9 23:44 
@Author      : SiYuan 
@Email       : siyuan044@qq.com 
@File        : TrailSnap-photo.py 
@Description : 
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from app.db.base import Base


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)

    filename = Column(String)
    uploaded_at = Column(DateTime)
    taken_at = Column(DateTime)
    lat = Column(Float)
    lon = Column(Float)
    location_name = Column(String)

    user = relationship("User", backref="photos")
    trip = relationship("Trip", backref="photos")
