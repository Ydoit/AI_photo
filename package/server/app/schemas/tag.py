from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class TagBase(BaseModel):
    tag_name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: UUID
    create_time: datetime
    
    class Config:
        from_attributes = True

class PhotoTagAdd(BaseModel):
    tag_name: str
    confidence: Optional[float] = 1.0

class PhotoTagResponse(BaseModel):
    id: UUID # tag id
    tag_name: str
    confidence: float
    
    class Config:
        from_attributes = True
