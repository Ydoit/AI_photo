from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class ImageDescription(Base):
    __tablename__ = "image_descriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    photo_id = Column(UUID(as_uuid=True), ForeignKey("photos.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    quality_score = Column(Float, nullable=True) # 0-100
    tags = Column(JSON, nullable=True) # List of tags
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    photo = relationship("Photo", back_populates="image_description")
