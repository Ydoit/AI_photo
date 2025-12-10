from sqlalchemy import Column, String, Integer, JSON, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import enum
import uuid
from app.db.base import Base

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(str, enum.Enum):
    SCAN_FOLDER = "SCAN_FOLDER"
    PROCESS_IMAGE = "PROCESS_IMAGE"
    GENERATE_THUMBNAIL = "GENERATE_THUMBNAIL"
    EXTRACT_METADATA = "EXTRACT_METADATA"
    CLASSIFY_IMAGE = "CLASSIFY_IMAGE"
    RECOGNIZE_FACE = "RECOGNIZE_FACE"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False)
    status = Column(String(20), default=TaskStatus.PENDING.value)
    priority = Column(Integer, default=0) # Higher number = Higher priority
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
