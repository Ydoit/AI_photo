#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/9 23:44 
@Author      : SiYuan 
@Email       : siyuan044@qq.com 
@File        : TrailSnap-person.py 
@Description : 
"""

from sqlalchemy import Column, Integer, String
from app.db.base import Base


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    embedding = Column(String)  # 存人脸编码（base64 或 JSON）
