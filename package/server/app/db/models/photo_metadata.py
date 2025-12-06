#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class PhotoMetadata(Base):
    __tablename__ = "photo_metadata"

    photo_id = Column(UUID(as_uuid=True), ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True)
    camera_info = Column(Text)  # EXIF info as text or JSON? Requirement says TEXT.
    location = Column(JSON)     # Using JSON for flexibility: {"lat": ..., "lng": ...} or POINT string
    tags = Column(JSON)         # List of tags
    faces = Column(JSON)        # List of face info

    photo = relationship("Photo", back_populates="metadata_info")
