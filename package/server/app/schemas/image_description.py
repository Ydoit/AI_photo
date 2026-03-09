from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class ImageDescriptionBase(BaseModel):
    description: Optional[str] = None
    memory_score: Optional[float] = None
    quality_score: Optional[float] = None
    tags: Optional[List[str]] = None
    reason: Optional[str] = None
    narrative: Optional[str] = None

class ImageDescription(ImageDescriptionBase):
    id: int
    photo_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
