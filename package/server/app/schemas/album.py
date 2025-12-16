from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, computed_field
from app.db.models.photo import FileType

# Metadata Schemas
class PhotoMetadataBase(BaseModel):
    exif_info: Optional[str] = None
    location_api: Optional[str] = None
    
    # Enhanced location fields
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    city: Optional[str] = None
    district: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None

class PhotoMetadataCreate(PhotoMetadataBase):
    pass

class PhotoMetadataUpdate(PhotoMetadataBase):
    pass

class PhotoMetadata(PhotoMetadataBase):
    photo_id: UUID

    class Config:
        from_attributes = True


# Photo Schemas
class PhotoBase(BaseModel):
    file_type: FileType
    size: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    filename: Optional[str] = None
    photo_time: Optional[datetime] = None

class PhotoCreate(PhotoBase):
    pass

class PhotoUpdate(BaseModel):
    filename: Optional[str] = None
    photo_time: Optional[datetime] = None

class Photo(PhotoBase):
    id: UUID
    # album_id removed from core Photo model, usually returned as separate list or part of details
    file_path: str = Field(exclude=True)
    upload_time: datetime
    # metadata_info: Optional[PhotoMetadata] = None
    album_ids: Optional[List[UUID]] = [] # Helper field for API response

    @computed_field
    def url(self) -> str:
        return f"/api/medias/{self.id}/file"

    @computed_field
    def thumbnail_url(self) -> str:
        return f"/api/medias/{self.id}/thumbnail"

    class Config:
        from_attributes = True

class PhotoGroup(BaseModel):
    date: str
    items: List[Photo]

class BatchPhotoUpdate(BaseModel):
    photo_ids: List[UUID]
    album_id: Optional[UUID] = None # For adding to album
    action: str # 'add_to_album', 'remove_from_album', 'delete'

class PhotoCreateItem(BaseModel):
    photo: PhotoCreate
    file_path: str
    metadata: Optional[PhotoMetadataCreate] = None
    photo_id: UUID

class BatchPhotoCreate(BaseModel):
    items: List[PhotoCreateItem]

# Album Schemas
class AlbumBase(BaseModel):
    name: str
    description: Optional[str] = None

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
    num_photos: int = 0
    # photos: List[Photo] = [] # Can be heavy if included by default.

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
