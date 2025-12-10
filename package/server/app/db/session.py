#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/9 23:45 
@Author      : SiYuan 
@Email       : siyuan044@qq.com 
@File        : TrailSnap-session.py 
@Description : 
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get('DB_URL')

engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # 先保留默认，后续再调
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # 定期回收空闲连接（避免失效连接）
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

