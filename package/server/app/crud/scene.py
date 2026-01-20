from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models.scene import Scene
from app.db.models.photo_metadata import PhotoMetadata
from app.schemas.scene import SceneCreate, SceneUpdate
from uuid import uuid4, UUID
from typing import List, Optional

def point_in_polygon(x, y, polygon):
    """
    Check if point (x, y) is inside the polygon.
    polygon: list of [x, y] points.
    """
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def update_scene_photos(db: Session, scene: Scene):
    """
    Update photos that fall within the scene's polygon.
    """
    if not scene.polygon:
        return

    # polygon is stored as [[lat, lng], ...] (list of lists)
    # Convert to [[lng, lat], ...] for point_in_polygon (x=lng, y=lat)
    poly_points = [[float(p[1]), float(p[0])] for p in scene.polygon]
    
    # Fetch all photos with location
    # Optimization: Filter by bounding box first if possible, but for now fetch all is safer/easier
    # given we don't have PostGIS. 
    # If dataset is huge, we should calculate bbox of polygon and filter by that first.
    
    min_lng = min(p[0] for p in poly_points)
    max_lng = max(p[0] for p in poly_points)
    min_lat = min(p[1] for p in poly_points)
    max_lat = max(p[1] for p in poly_points)

    photos = db.query(PhotoMetadata).filter(
        PhotoMetadata.latitude >= min_lat,
        PhotoMetadata.latitude <= max_lat,
        PhotoMetadata.longitude >= min_lng,
        PhotoMetadata.longitude <= max_lng
    ).all()
    
    updated_count = 0
    for photo in photos:
        if point_in_polygon(float(photo.longitude), float(photo.latitude), poly_points):
            photo.scene_id = scene.id
            updated_count += 1
            
    if updated_count > 0:
        db.commit()

def create_scene(db: Session, scene: SceneCreate):
    db_scene = Scene(
        id=uuid4(),
        **scene.model_dump()
    )
    db.add(db_scene)
    db.commit()
    db.refresh(db_scene)
    
    update_scene_photos(db, db_scene)
    
    return db_scene

def get_scenes(db: Session, skip: int = 0, limit: int = 100):
    results = db.query(
        Scene,
        func.count(PhotoMetadata.photo_id).label("photo_count")
    ).outerjoin(
        PhotoMetadata, Scene.id == PhotoMetadata.scene_id
    ).group_by(
        Scene.id
    ).offset(skip).limit(limit).all()
    
    scenes = []
    for scene, count in results:
        scene.photo_count = count
        scenes.append(scene)
    return scenes

def get_scene(db: Session, scene_id: UUID):
    return db.query(Scene).filter(Scene.id == scene_id).first()

def delete_scene(db: Session, scene_id: UUID):
    db_scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if db_scene:
        if not db_scene.is_custom:
            raise ValueError("Cannot delete system default scene")
            
        # Clear scene_id from photos?
        # ForeignKey has ondelete set? 
        # Check PhotoMetadata model: scene_id = Column(UUID(as_uuid=True), ForeignKey("scenes.id"), nullable=True)
        # It doesn't specify ondelete="SET NULL" explicitly in the Column definition, 
        # but usually SQLAlchemy handles this if relationship is configured.
        # Actually, let's just let DB handle it or manually set null.
        # Ideally we want to set null.
        
        photos = db.query(PhotoMetadata).filter(PhotoMetadata.scene_id == scene_id).all()
        for p in photos:
            p.scene_id = None
            
        db.delete(db_scene)
        db.commit()
    return db_scene

def update_scene(db: Session, scene_id: UUID, scene: SceneUpdate):
    db_scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not db_scene:
        return None
    
    update_data = scene.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_scene, key, value)
        
    db.add(db_scene)
    db.commit()
    db.refresh(db_scene)
    
    # If polygon or location changed, we might need to re-evaluate photos?
    # For now, let's re-run update_scene_photos if polygon changed.
    if 'polygon' in update_data:
        update_scene_photos(db, db_scene)
        
    return db_scene
