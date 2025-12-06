#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/8/10 22:29 
@Author      : SiYuan 
@Email       : siyuan044@gmail.com
@File        : backend-album.py 
@Description : 
"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.base import Base


class Album(Base):
    """
    相册表
    """
    __tablename__ = 'albums'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    create_time = Column(DateTime, default=datetime.now)
    description = Column(Text)
    
    # 1:N relationship with Photo
    photos = relationship("Photo", back_populates="album", cascade="all, delete-orphan")


if __name__ == '__main__':
    pass
