from typing import List, Optional, Any
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal

class SceneBase(BaseModel):
    name: str
    description: Optional[str] = None
    level: Optional[int] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius: Optional[int] = None
    polygon: Optional[List[List[float]]] = None

class SceneCreate(SceneBase):
    pass

class SceneUpdate(SceneBase):
    pass

class Scene(SceneBase):
    id: UUID
    
    class Config:
        from_attributes = True
