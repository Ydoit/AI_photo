from typing import Optional, List
from pydantic import BaseModel
from app.schemas.photo import Photo

class LocationBase(BaseModel):
    name: str
    level: str
    count: int

class LocationStatistics(BaseModel):
    province_count: int
    city_count: int
    district_count: int
    country_count: int

class Location(LocationBase):
    id: Optional[str] = None
    is_custom: Optional[bool] = None
    cover: Optional[Photo] = None

    class Config:
        from_attributes = True

class MapMarker(BaseModel):
    id: str
    lat: float
    lng: float

class LocationValue(BaseModel):
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None

class LocationSearchItem(BaseModel):
    label: str
    value: LocationValue
