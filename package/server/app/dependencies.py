#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/10 22:31 
@Author      : SiYuan 
@Email       : sixyuan044@gmail.com 
@File        : backend-dependencies.py 
@Description : 
"""
from app.db.base import Base
import app.db.models
from app.db.session import SessionLocal, engine
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
