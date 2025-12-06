from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.db.models.photo import FileType

# Metadata Schemas
class PhotoMetadataBase(BaseModel):
    camera_info: Optional[str] = None
    location: Optional[Dict[str, Any]] = None # {"lat": float, "lng": float}
    tags: Optional[List[str]] = None
    faces: Optional[List[Dict[str, Any]]] = None

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

class PhotoCreate(PhotoBase):
    pass

class Photo(PhotoBase):
    id: UUID
    album_id: Optional[UUID] = None
    file_path: str
    upload_time: datetime
    metadata_info: Optional[PhotoMetadata] = None

    class Config:
        from_attributes = True

class BatchPhotoUpdate(BaseModel):
    photo_ids: List[UUID]
    action: str # 'move_to_album', 'delete'
    target_album_id: Optional[UUID] = None


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
    photos: List[Photo] = []

    class Config:
        from_attributes = True
