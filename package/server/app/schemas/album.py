from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, computed_field
from app.schemas.photo import Photo

# Album Schemas
class AlbumBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = "user"
    condition: Optional[Dict[str, Any]] = None
    threshold: Optional[float] = 0.25

class AlbumCreate(AlbumBase):
    pass

class AlbumUpdate(AlbumBase):
    name: Optional[str] = None
    description: Optional[str] = None

class Album(AlbumBase):
    id: UUID
    create_time: datetime
    cover: Optional[Photo] = None
    type: str = "user"
    condition: Optional[Dict[str, Any]] = None
    num_photos: int = 0
    threshold: Optional[float] = 0.25

    class Config:
        from_attributes = True

class TimelineItem(BaseModel):
    year: int
    month: int
    day: int
    count: int

class TimelineStats(BaseModel):
    total_photos: int
    time_range: Optional[Dict[str, datetime]] = None
    timeline: List[TimelineItem] = []