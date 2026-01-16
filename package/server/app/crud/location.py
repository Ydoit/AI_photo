from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.models.photo import Photo
from app.db.models.photo_metadata import PhotoMetadata
from app.db.models.scene import Scene

def get_locations(db: Session, level: str = 'city', skip: int = 0, limit: int = 100):
    is_scene = False
    if level == 'city':
        group_col = PhotoMetadata.city
    elif level == 'province':
        group_col = PhotoMetadata.province
    elif level == 'district':
        group_col = PhotoMetadata.district
    elif level == 'scene':
        group_col = Scene.name
        is_scene = True
    else:
        return []

    # Group by location and count
    query = db.query(
        group_col,
        func.count(Photo.id).label('count')
    ).join(
        PhotoMetadata, Photo.id == PhotoMetadata.photo_id
    )

    if is_scene:
        query = query.join(Scene, PhotoMetadata.scene_id == Scene.id)

    query = query.filter(
        group_col.is_not(None),
        group_col != ''
    ).group_by(
        group_col
    ).order_by(
        desc('count')
    ).offset(skip).limit(limit)

    results = query.all()

    if not results:
        return []

    # Get list of location names from current page results
    names = [r[0] for r in results]

    # Batch fetch cover photos using DISTINCT ON to avoid N+1 queries
    # Optimized for PostgreSQL
    cover_query = db.query(
        Photo,
        group_col
    ).join(
        PhotoMetadata, Photo.id == PhotoMetadata.photo_id
    )
    
    if is_scene:
        cover_query = cover_query.join(Scene, PhotoMetadata.scene_id == Scene.id)

    covers = cover_query.filter(
        group_col.in_(names)
    ).distinct(
        group_col
    ).order_by(
        group_col,
        desc(Photo.photo_time)
    ).all()

    # Map location name to cover photo
    cover_map = {loc_name: photo for photo, loc_name in covers}

    locations = []
    for name, count in results:
        locations.append({
            "name": name,
            "level": level,
            "count": count,
            "cover": cover_map.get(name)
        })
        
    return locations

def get_location_photos(db: Session, name: str, level: str = 'city', skip: int = 0, limit: int = 50):
    if level == 'city':
        col = PhotoMetadata.city
        query = db.query(Photo).join(PhotoMetadata, Photo.id == PhotoMetadata.photo_id)
    elif level == 'province':
        col = PhotoMetadata.province
        query = db.query(Photo).join(PhotoMetadata, Photo.id == PhotoMetadata.photo_id)
    elif level == 'district':
        col = PhotoMetadata.district
        query = db.query(Photo).join(PhotoMetadata, Photo.id == PhotoMetadata.photo_id)
    elif level == 'scene':
        col = Scene.name
        query = db.query(Photo).join(PhotoMetadata, Photo.id == PhotoMetadata.photo_id)\
                  .join(Scene, PhotoMetadata.scene_id == Scene.id)
    else:
        return []
        
    return query.filter(
        col == name
    ).order_by(
        desc(Photo.photo_time)
    ).offset(skip).limit(limit).all()

def get_map_markers(db: Session):
    results = db.query(
        Photo.id,
        PhotoMetadata.latitude,
        PhotoMetadata.longitude
    ).join(PhotoMetadata, Photo.id == PhotoMetadata.photo_id)\
     .filter(PhotoMetadata.latitude.isnot(None))\
     .filter(PhotoMetadata.longitude.isnot(None))\
     .all()
     
    return [
        {"id": str(r[0]), "lat": float(r[1]), "lng": float(r[2])}
        for r in results
    ]

def get_location_distribution(db: Session, level: str = 'city'):
    is_scene = False
    if level == 'city':
        group_col = PhotoMetadata.city
    elif level == 'province':
        group_col = PhotoMetadata.province
    elif level == 'district':
        group_col = PhotoMetadata.district
    elif level == 'scene':
        group_col = Scene.name
        is_scene = True
    else:
        return []

    # Group by location and count, no limit
    query = db.query(
        group_col.label('name'),
        func.count(Photo.id).label('count')
    ).join(
        PhotoMetadata, Photo.id == PhotoMetadata.photo_id
    )

    if is_scene:
        query = query.join(Scene, PhotoMetadata.scene_id == Scene.id)

    results = query.filter(
        group_col.is_not(None),
        group_col != ''
    ).group_by(
        group_col
    ).all()
    
    return [{"name": r[0], "count": r[1], "level": level} for r in results]

def get_location_statistics(db: Session):
    province_count = db.query(func.count(func.distinct(PhotoMetadata.province))).filter(PhotoMetadata.province != '', PhotoMetadata.province.is_not(None)).scalar()
    city_count = db.query(func.count(func.distinct(PhotoMetadata.city))).filter(PhotoMetadata.city != '', PhotoMetadata.city.is_not(None)).scalar()
    district_count = db.query(func.count(func.distinct(PhotoMetadata.district))).filter(PhotoMetadata.district != '', PhotoMetadata.district.is_not(None)).scalar()
    country_count = db.query(func.count(func.distinct(PhotoMetadata.country))).filter(PhotoMetadata.country != '', PhotoMetadata.country.is_not(None)).scalar()
    
    return {
        "province_count": province_count,
        "city_count": city_count,
        "district_count": district_count,
        "country_count": country_count
    }
