from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.dependencies import get_db
from app.db.models.face import FaceIdentity, Face
from app.db.models.photo import Photo
from app.schemas import album
from app.core.config_manager import config_manager
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

router = APIRouter()

class CoverPhotoInfo(BaseModel):
    photo_id: UUID = Field(..., description="封面照片ID")
    width: Optional[int] = Field(None, description="照片宽度")
    height: Optional[int] = Field(None, description="照片高度")
    face_rect: Optional[List[float]] = Field(None, description="人脸位置坐标 [x1, y1, x2, y2]")

class FaceIdentitySchema(BaseModel):
    id: UUID = Field(..., description="人物ID")
    identity_name: Optional[str] = Field(None, description="人物名称")
    default_face_id: Optional[int] = Field(None, description="默认封面人脸ID")
    face_count: Optional[int] = Field(0, description="照片数量")
    cover_photo: Optional[CoverPhotoInfo] = Field(None, description="封面照片信息")

    class Config:
        from_attributes = True

class FaceIdentityUpdate(BaseModel):
    name: str = Field(..., description="新的名称")

class MergeRequest(BaseModel):
    source_ids: List[UUID] = Field(..., description="源人物ID列表")
    target_id: UUID = Field(..., description="目标人物ID")

class RemovePhotosRequest(BaseModel):
    photo_ids: List[UUID] = Field(..., description="要移除的照片ID列表")

class SetCoverRequest(BaseModel):
    photo_id: UUID = Field(..., description="设置为封面的照片ID")

@router.get("/identities", response_model=List[FaceIdentitySchema], summary="获取人物列表", description="获取所有已识别的人物列表，支持分页，返回包含封面信息和照片数量的人物对象")
def list_identities(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=10000, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取人物列表，包含每个人的封面照片和照片总数。
    """
    offset = (page - 1) * limit
    
    # Subquery for face counts to avoid N+1 queries
    face_counts = db.query(
        Face.face_identity_id,
        func.count(Face.id).label("count")
    ).filter(
        Face.is_deleted == False,
        Face.face_identity_id != None
    ).group_by(Face.face_identity_id).subquery()

    # Main query: Identity + Count + Default Face + Photo
    query = db.query(
        FaceIdentity,
        face_counts.c.count,
        Face,
        Photo
    ).outerjoin(
        face_counts, FaceIdentity.id == face_counts.c.face_identity_id
    ).outerjoin(
        Face, FaceIdentity.default_face_id == Face.id
    ).outerjoin(
        Photo, Face.photo_id == Photo.id
    ).filter(
        FaceIdentity.is_deleted == False
    ).order_by(
        FaceIdentity.create_time.desc()
    ).offset(offset).limit(limit)
    results = []
    for identity, count, default_face, photo in query.all():
        if count<=config_manager.config.ai.face_recognition_min_photos:
            continue
        cover = None
        if default_face and photo:
            cover = CoverPhotoInfo(
                photo_id=default_face.photo_id,
                width=photo.width,
                height=photo.height,
                face_rect=default_face.face_rect
            )
        results.append({
            "id": identity.id,
            "identity_name": identity.identity_name,
            "default_face_id": identity.default_face_id,
            "face_count": count or 0,
            "cover_photo": cover
        })
    return results


@router.get("/identities/{id}/photos", response_model=List[album.Photo], summary="获取人物照片列表", description="获取指定人物下的所有照片")
def get_identity_photos(
    id: UUID = Path(..., description="人物ID"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(50, ge=1, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取指定人物关联的所有照片列表。
    """
    offset = (page - 1) * limit
    photos = db.query(Photo).join(Face).filter(
        Face.face_identity_id == id,
        Photo.id == Face.photo_id,
        Face.is_deleted == False
    ).offset(offset).limit(limit).all()

    return photos

@router.delete("/identities/{id}", summary="删除人物", description="软删除指定人物，但保留其关联的照片（解除关联）")
def delete_identity(
    id: UUID = Path(..., description="人物ID"),
    db: Session = Depends(get_db)
):
    """
    删除人物。
    注意：这只是软删除人物记录，并将关联的人脸数据中的 identity_id 置为 NULL（解除关联）。
    """
    identity = db.query(FaceIdentity).get(id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    # Dissociate faces
    faces = db.query(Face).filter(Face.face_identity_id == id).all()
    for face in faces:
        face.face_identity_id = None

    # Soft delete identity
    identity.is_deleted = True
    
    db.commit()
    return {"status": "success"}

@router.post("/identities/{id}/remove-photos", summary="从人物中移除照片", description="将指定照片从该人物中移除（解除人脸关联）")
def remove_photos_from_identity(
    id: UUID = Path(..., description="人物ID"),
    payload: RemovePhotosRequest = Body(..., description="要移除的照片列表"),
    db: Session = Depends(get_db)
):
    """
    批量从人物中移除照片。
    """
    identity = db.query(FaceIdentity).get(id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
        
    # Find faces in these photos that belong to this identity
    faces = db.query(Face).filter(
        Face.face_identity_id == id,
        Face.photo_id.in_(payload.photo_ids)
    ).all()
    
    for face in faces:
        face.face_identity_id = None # Dissociate
        
    db.commit()
    return {"status": "success", "count": len(faces)}

@router.put("/identities/{id}/cover", summary="设置人物封面", description="将指定照片设为该人物的封面照片")
def set_identity_cover(
    id: UUID = Path(..., description="人物ID"),
    payload: SetCoverRequest = Body(..., description="封面设置请求"),
    db: Session = Depends(get_db)
):
    """
    设置人物的封面照片。
    系统会自动查找该照片中属于该人物的人脸，并将其ID设为默认人脸ID。
    """
    identity = db.query(FaceIdentity).get(id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
        
    # Find face in the photo belonging to this identity
    face = db.query(Face).filter(
        Face.face_identity_id == id,
        Face.photo_id == payload.photo_id
    ).first()
    
    if not face:
        raise HTTPException(status_code=404, detail="Face not found in this photo for this identity")
        
    identity.default_face_id = face.id
    db.commit()
    return {"status": "success"}

@router.put("/identities/{id}/name", summary="重命名人物", description="修改人物的显示名称")
def rename_identity(
    id: UUID = Path(..., description="人物ID"),
    payload: FaceIdentityUpdate = Body(..., description="重命名请求"),
    db: Session = Depends(get_db)
):
    """
    修改人物名称。
    """
    identity = db.query(FaceIdentity).get(id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    identity.identity_name = payload.name
    db.commit()
    return {"status": "success", "name": payload.name}

@router.post("/identities/merge", summary="合并人物", description="将多个源人物合并到一个目标人物中")
def merge_identities(
    payload: MergeRequest = Body(..., description="合并请求"),
    db: Session = Depends(get_db)
):
    """
    合并人物。
    将源人物的所有人脸数据移动到目标人物下，并软删除源人物。
    """
    target = db.query(FaceIdentity).get(payload.target_id)
    if not target:
         raise HTTPException(status_code=404, detail="Target identity not found")
         
    for source_id in payload.source_ids:
        if source_id == payload.target_id:
            continue
            
        source = db.query(FaceIdentity).get(source_id)
        if not source:
            continue
            
        # Move faces
        faces = db.query(Face).filter(Face.face_identity_id == source_id).all()
        for face in faces:
            face.face_identity_id = payload.target_id
            
        # Soft delete source
        source.is_deleted = True
        
    db.commit()
    return {"status": "success"}
