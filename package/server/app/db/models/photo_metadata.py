#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class PhotoMetadata(Base):
    __tablename__ = "photo_metadata"

    photo_id = Column(UUID(as_uuid=True), ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True)
    exif_info = Column(Text)    # EXIF info as text
    location = Column(JSON)     # Using JSON for flexibility: {"lat": ..., "lng": ..., "formatted_address": ...}
    location_api = Column(String(255)) # API info for location
    tags = Column(JSON)         # List of tags
    faces = Column(JSON)        # List of face info

    photo = relationship("Photo", back_populates="metadata_info")
