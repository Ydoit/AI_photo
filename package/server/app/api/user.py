#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/10 22:33 
@Author      : SiYuan 
@Email       : sixyuan044@gmail.com 
@File        : server-user.py 
@Description : 
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserRead
from app.crud.user import create_user
from app.dependencies import get_db

router = APIRouter()


@router.post("/", response_model=UserRead)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)


@router.get("/", response_model=UserRead)
def create_new_user(db: Session = Depends(get_db)):
    return create_user(db, None)
