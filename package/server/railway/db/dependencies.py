#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/18 21:18
@Author      : SiYuan
@Email       : sixyuan044@gmail.com
@File        : server-dependencies.py
@Description : 
"""

from railway.db.base import Base
from railway.db.models import Station, TrainOperationPlan, Train, TrainSchedule
from railway.db.session import SessionLocal, engine
from sqlalchemy.orm import Session

# 创建数据库表！！！
Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)