#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/10 22:33 
@Author      : SiYuan 
@Email       : siyuan044@qq.com 
@File        : backend-user.py 
@Description : 
"""

from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str

class UserRead(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True
