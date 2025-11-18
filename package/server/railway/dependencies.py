#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/18 21:18
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-dependencies.py
@Description : 
"""

from railway.db.base import Base
from railway.db import models
from railway.db.session import SessionLocal, engine
from sqlalchemy.orm import Session

# 创建数据库表！！！必须放在User后面
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()