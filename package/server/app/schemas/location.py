from typing import Optional, List
from pydantic import BaseModel
from app.schemas.photo import Photo

class LocationBase(BaseModel):
    name: str
    level: str
    count: int

class Location(LocationBase):
    cover: Optional[Photo] = None

    class Config:
        from_attributes = True
