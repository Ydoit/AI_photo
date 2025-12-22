#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/9 23:45 
@Author      : SiYuan 
@Email       : sixyuan044@gmail.com 
@File        : TrailSnap-init_db.py 
@Description : 
"""

from app.db.session import engine
import app.db.models
from app.db.base import Base


def init_models():
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库初始化完成")

if __name__ == "__main__":
    init_models()

