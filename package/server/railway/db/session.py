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

RAILWAY_DB_URL = os.getenv("RAILWAY_DB_URL", "")
if not RAILWAY_DB_URL:
    raise ValueError("RAILWAY_DB_URL environment variable is not set")
engine = create_engine(RAILWAY_DB_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)