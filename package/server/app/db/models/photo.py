#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, BigInteger, Integer, Enum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class FileType(enum.Enum):
    image = 'image'
    video = 'video'
    live_photo = 'live_photo'

class Photo(Base):
    __tablename__ = "photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255))
    photo_time = Column(DateTime)
    file_path = Column(String(255), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    upload_time = Column(DateTime, default=datetime.now)
    size = Column(BigInteger)
    width = Column(Integer)
    height = Column(Integer)
    duration = Column(Float, default=0)

    # Relationships
    albums = relationship("Album", secondary="album_photos", back_populates="photos")
    metadata_info = relationship("PhotoMetadata", uselist=False, back_populates="photo", cascade="all, delete-orphan")

    @property
    def album_ids(self):
        return [str(album.id) for album in self.albums]
