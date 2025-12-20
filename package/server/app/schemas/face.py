from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

# Face Schemas
class FaceBase(BaseModel):
    face_rect: Optional[List[float]] = None
    face_confidence: Optional[float] = None
    recognize_confidence: Optional[float] = None
    face_feature: Optional[Any] = None

class FaceCreate(FaceBase):
    photo_id: UUID
    face_identity_id: Optional[UUID] = None

class FaceUpdate(FaceBase):
    face_identity_id: Optional[UUID] = None

class Face(FaceBase):
    id: int
    photo_id: UUID
    face_identity_id: Optional[UUID] = None
    create_time: datetime
    update_time: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

# FaceIdentity Schemas
class FaceIdentityBase(BaseModel):
    identity_name: Optional[str] = None

class FaceIdentityCreate(FaceIdentityBase):
    pass

class FaceIdentityUpdate(FaceIdentityBase):
    default_face_id: Optional[int] = None

class FaceIdentity(FaceIdentityBase):
    id: UUID
    default_face_id: Optional[int] = None
    create_time: datetime
    update_time: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class CoverPhotoInfo(BaseModel):
    photo_id: UUID = Field(..., description="封面照片ID")
    width: Optional[int] = Field(None, description="照片宽度")
    height: Optional[int] = Field(None, description="照片高度")
    face_rect: Optional[List[float]] = Field(None, description="人脸位置坐标 [x1, y1, x2, y2]")

class FaceIdentityDetail(FaceIdentity):
    face_count: int = 0
    cover_photo: Optional[CoverPhotoInfo] = None
