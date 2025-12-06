#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, BigInteger, Integer, Enum
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
    album_id = Column(UUID(as_uuid=True), ForeignKey("albums.id", ondelete="CASCADE"), nullable=True)
    file_path = Column(String(255), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    upload_time = Column(DateTime, default=datetime.now)
    size = Column(BigInteger)
    width = Column(Integer)
    height = Column(Integer)

    # Relationships
    album = relationship("Album", back_populates="photos")
    metadata_info = relationship("PhotoMetadata", uselist=False, back_populates="photo", cascade="all, delete-orphan")
