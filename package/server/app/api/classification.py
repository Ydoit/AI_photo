from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.dependencies import get_db
from app.schemas import tag as schemas
from app.crud import tag as crud
from app.schemas import photo as photo_schemas

router = APIRouter()

@router.get("", response_model=List[schemas.TagStats], summary="获取智能分类标签列表")
def get_tags(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取智能分类标签列表，包含每个标签的封面图片和照片数量。
    """
    return crud.get_tags_with_stats(db, skip, limit)

@router.get("/{name}/photos", response_model=List[photo_schemas.Photo], summary="获取分类照片列表")
def get_tag_photos(
    name: str = Path(..., description="标签名称"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取指定标签分类的照片列表。
    """
    photos = crud.get_photos_by_tag_name(db, name, skip, limit)
    return photos
