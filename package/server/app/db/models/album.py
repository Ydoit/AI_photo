#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/8/10 22:29 
@Author      : SiYuan 
@Email       : siyuan044@gmail.com
@File        : backend-album.py 
@Description : 
"""
from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Album(Base):
    """
    相册表
    用户自定义相册（可按主题、地点等分类）
    """
    __tablename__ = 'albums'
    id = Column(Integer, primary_key=True)                 # 主键
    name = Column(String, nullable=False)                  # 相册名称
    created_at = Column(DateTime)                          # 创建时间
    description = Column(Text)                             # 相册描述
    media_items = relationship('Media', secondary='album_media', back_populates='albums')

class AlbumMedia(Base):
    """
    相册-媒体关联表
    用于将相册与多张媒体文件关联
    """
    __tablename__ = 'album_media'
    album_id = Column(Integer, ForeignKey('albums.id'), primary_key=True) # 相册ID
    media_id = Column(Integer, ForeignKey('media.id'), primary_key=True)  # 媒体ID


if __name__ == '__main__':
    pass
