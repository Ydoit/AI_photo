#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/11/18 21:15
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-session.py
@Description : 
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./data/railway_db.db"  # SQLite数据库路径
DATABASE_URL = "postgresql://msi:msi4090@192.168.1.113:5532/railway"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)