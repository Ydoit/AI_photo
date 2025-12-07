import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.db.base import Base

class AppSetting(Base):
    __tablename__ = 'app_settings'
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

