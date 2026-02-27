from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas import album
from app.schemas import face as schemas
from app.crud import face as crud_face
from app.core.config_manager import config_manager
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

from app.schemas.face import FaceIdentitySchema, RemovePhotosRequest, SetCoverRequest, MergeRequest

router = APIRouter()

from app.service.face_cluster import FaceClusterService

@router.put("/identities/{id}", summary="更新人物信息", description="修改人物的显示名称、描述和标签")
def update_identity(
    id: UUID = Path(..., description="人物ID"),
    payload: schemas.FaceIdentityUpdate = Body(..., description="人物更新信息"),
    db: Session = Depends(get_db)
):
    """
    更新人物信息（名称、描述、标签）。
    """
    if not crud_face.get_identity(db, id):
        raise HTTPException(status_code=404, detail="Identity not found")

    updated_identity = crud_face.update_identity(db, id, payload)
    return updated_identity

@router.get("/identities", response_model=List[FaceIdentitySchema], summary="获取人物列表", description="获取所有已识别的人物列表，支持分页，返回包含封面信息和照片数量的人物对象")
def list_identities(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=10000, description="每页数量"),
    types: List[str] = Query(["named", "unnamed"], alias="types[]" , description="人物类型筛选：named, unnamed, hidden"),
    db: Session = Depends(get_db)
):
    """
    获取人物列表，包含每个人的封面照片和照片总数。
    """
    offset = (page - 1) * limit
    min_photos = config_manager.config.ai.face_recognition_min_photos
    print(types)
    return crud_face.get_identities_with_details(
        db,
        skip=offset,
        limit=limit,
        min_photos=min_photos,
        visibility_types=types
    )


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
    return crud_face.get_identity_photos(db, id, skip=offset, limit=limit)

@router.delete("/identities/{id}", summary="删除人物", description="软删除指定人物，但保留其关联的照片（解除关联）")
def delete_identity(
    id: UUID = Path(..., description="人物ID"),
    db: Session = Depends(get_db)
):
    """
    删除人物。
    注意：这只是软删除人物记录，并将关联的人脸数据中的 identity_id 置为 NULL（解除关联）。
    """
    if not crud_face.delete_identity(db, id):
        raise HTTPException(status_code=404, detail="Identity not found")
    
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
    if not crud_face.get_identity(db, id):
        raise HTTPException(status_code=404, detail="Identity not found")
        
    count = crud_face.remove_photos_from_identity(db, id, payload.photo_ids)
    return {"status": "success", "count": count}

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
    if not crud_face.get_identity(db, id):
        raise HTTPException(status_code=404, detail="Identity not found")
        
    if not crud_face.set_identity_cover(db, id, payload.photo_id):
        raise HTTPException(status_code=404, detail="Face not found in this photo for this identity")
        
    return {"status": "success"}

@router.post("/identities/merge", summary="合并人物", description="将多个源人物合并到一个目标人物中")
def merge_identities(
    payload: MergeRequest = Body(..., description="合并请求"),
    db: Session = Depends(get_db)
):
    """
    合并人物。
    """
    if not crud_face.merge_identities(db, payload.target_id, payload.source_ids):
         raise HTTPException(status_code=400, detail="Merge failed")
    
    return {"status": "success"}

@router.post("/identities/{id}/rescan", summary="重新扫描人物人脸", description="根据当前人物的人脸中心，重新扫描未分配的人脸并尝试关联")
def rescan_identity(
    id: UUID = Path(..., description="人物ID"),
    db: Session = Depends(get_db)
):
    """
    重新扫描人物人脸，将符合条件的人脸关联到该人物。
    """
    if not crud_face.get_identity(db, id):
        raise HTTPException(status_code=404, detail="Identity not found")
        
    service = FaceClusterService(db)
    count = service.rescan_identity(id)
    return {"status": "success", "count": count}
