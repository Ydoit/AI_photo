from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.db.models import User
from app.dependencies import get_db
from app.schemas import tag as schemas
from app.crud import tag as crud
from app.schemas import photo as photo_schemas

router = APIRouter()

@router.get("", response_model=List[schemas.TagStats], summary="获取智能分类标签列表")
def get_tags(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    获取智能分类标签列表，包含每个标签的封面图片和照片数量。
    """
    return crud.get_tags_with_stats(db, current_user.id, skip, limit)

# 核心改造：{path:path} 匹配包含/的全部剩余路径
@router.get("/{path:path}/photos", response_model=List[photo_schemas.Photo], summary="获取分类照片列表")
def get_tag_photos(
    # path=True 声明：匹配剩余的全部路径（支持包含/）
    path: str = Path(..., description="标签名称（支持多级/包含/）", path=True),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    # 注意：参数名从name改为path，传给crud层即可
    photos = crud.get_photos_by_tag_name(db, current_user.id, path, skip, limit)
    return photos
