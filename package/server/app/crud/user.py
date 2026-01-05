#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/10 22:34 
@Author      : SiYuan 
@Email       : sixyuan044@gmail.com 
@File        : server-user.py 
@Description : 
"""

from sqlalchemy.orm import Session
from app.db.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, user: UserCreate):
    db_user = User(username='123',email='123@123')
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
