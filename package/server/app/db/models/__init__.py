#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/5/9 23:44 
@Author      : SiYuan 
@Email       : sixyuan044@gmail.com 
@File        : TrailSnap-__init__.py.py 
@Description : 
"""
from app.db.models.album import Album
from app.db.models.photo import Photo, FileType
from app.db.models.photo_metadata import PhotoMetadata
from app.db.models.album_photos import AlbumPhoto
from app.db.models.trip import TicketType, TrainTicket
from app.db.models.user import User
from app.db.models.app_setting import AppSetting
from app.db.models.index_log import IndexLog
from app.db.models.task import Task, TaskStatus, TaskType
from app.db.models.face import Face, FaceIdentity
from app.db.models.tag import PhotoTag, PhotoTagRelation

if __name__ == '__main__':
    pass
