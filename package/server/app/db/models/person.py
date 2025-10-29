#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/9 23:44 
@Author      : SiYuan 
@Email       : siyuan044@qq.com 
@File        : TrailSnap-person.py 
@Description : 
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.db.base import Base


class Person(Base):
    """
    人物信息表
    存储识别到的人物（可以是已知姓名或AI识别标识）
    """
    __tablename__ = 'persons'
    id = Column(Integer, primary_key=True)                 # 主键
    name = Column(String)                                  # 人物名称（可为空）
    media_items = relationship('Media', secondary='person_media', back_populates='persons')

class PersonMedia(Base):
    """
    人物-媒体关联表（多对多）
    记录某张媒体中包含哪些人物，以及人物所在位置（人脸框）
    """
    __tablename__ = 'person_media'
    person_id = Column(Integer, ForeignKey('persons.id'), primary_key=True) # 人物ID
    media_id = Column(Integer, ForeignKey('media.id'), primary_key=True)    # 媒体ID
    x = Column(Float)    # 人脸框左上角X坐标（相对比例）
    y = Column(Float)    # 人脸框左上角Y坐标（相对比例）
    width = Column(Float)  # 人脸框宽度（相对比例）
    height = Column(Float) # 人脸框高度（相对比例）
