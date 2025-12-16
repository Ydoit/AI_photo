#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, DECIMAL, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base

class FaceIdentity(Base):
    __tablename__ = "face_identities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identity_name = Column(String(50))
    # use_alter=True to handle circular dependency during creation
    default_face_id = Column(Integer, ForeignKey("faces.id", use_alter=True), nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    faces = relationship("Face", back_populates="identity", foreign_keys="Face.face_identity_id")

class Face(Base):
    __tablename__ = "faces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    photo_id = Column(UUID(as_uuid=True), ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    face_identity_id = Column(UUID(as_uuid=True), ForeignKey("face_identities.id"), nullable=True)
    face_feature = Column(JSON)  # Human face feature vector
    face_rect = Column(JSON)     # Face rectangle coordinates: {"x1":..., "y1":..., "x2":..., "y2":...}
    face_confidence = Column(DECIMAL(5, 4))
    recognize_confidence = Column(DECIMAL(5, 4))
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    photo = relationship("Photo", back_populates="faces")
    identity = relationship("FaceIdentity", back_populates="faces", foreign_keys=[face_identity_id])
