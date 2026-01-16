from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import List
from app.dependencies import get_db
from app.schemas import location as schemas
from app.crud import location as crud
from app.schemas import photo as photo_schemas
from app.schemas import scene as scene_schemas
from app.crud import scene as scene_crud

router = APIRouter()

@router.get("", response_model=List[schemas.Location], summary="获取位置列表")
def get_locations(
    level: str = Query('city', regex='^(city|province|district|scene)$', description="分组级别：city 或 province 或 district 或 scene"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取按城市或省份分组的位置列表，包含每个位置的封面照片和照片数量。
    """
    return crud.get_locations(db, level, skip, limit)

@router.get("/distribution", response_model=List[schemas.LocationBase], summary="获取位置分布数据")
def get_location_distribution(
    level: str = Query('city', regex='^(city|province|district|scene)$', description="分组级别：city 或 province 或 district 或 scene"),
    db: Session = Depends(get_db)
):
    """
    获取所有位置的分布数据（仅包含名称和数量），用于地图展示。
    """
    return crud.get_location_distribution(db, level)

@router.get("/statistics", response_model=schemas.LocationStatistics, summary="获取位置统计数据")
def get_location_statistics(db: Session = Depends(get_db)):
    """
    获取位置统计数据（省份、城市、区县数量等）。
    """
    return crud.get_location_statistics(db)

@router.get("/markers", response_model=List[schemas.MapMarker], summary="获取地图标记点")
def get_map_markers(db: Session = Depends(get_db)):
    """
    获取所有包含GPS信息的照片标记点。
    """
    return crud.get_map_markers(db)

@router.post("/scenes", response_model=scene_schemas.Scene, summary="创建景区")
def create_scene(
    scene: scene_schemas.SceneCreate,
    db: Session = Depends(get_db)
):
    """
    创建新的景区，并自动关联范围内的照片。
    """
    return scene_crud.create_scene(db, scene)

@router.get("/scenes/list", response_model=List[scene_schemas.Scene], summary="获取所有景区详情")
def get_scenes_list(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取所有景区详细信息（包含多边形坐标）。
    """
    return scene_crud.get_scenes(db, skip, limit)

@router.get("/{name}/photos", response_model=List[photo_schemas.Photo], summary="获取位置照片列表")
def get_location_photos(
    name: str = Path(..., description="位置名称"),
    level: str = Query('city', regex='^(city|province|district|scene)$', description="分组级别：city 或 province 或 district 或 scene"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取指定位置（城市或省份）的照片列表。
    """
    return crud.get_location_photos(db, name, level, skip, limit)
