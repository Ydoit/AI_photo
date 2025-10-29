#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/10 22:31 
@Author      : SiYuan 
@Email       : siyuan044@qq.com 
@File        : backend-dependencies.py 
@Description : 
"""

from app.db.base import SessionLocal, Base, engine
from sqlalchemy.orm import Session

# 创建数据库表！！！必须放在User后面
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
