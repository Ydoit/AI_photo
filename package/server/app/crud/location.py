from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.models.photo import Photo
from app.db.models.photo_metadata import PhotoMetadata

def get_locations(db: Session, level: str = 'city', skip: int = 0, limit: int = 100):
    if level == 'city':
        group_col = PhotoMetadata.city
    elif level == 'province':
        group_col = PhotoMetadata.province
    elif level == 'district':
        group_col = PhotoMetadata.district
    else:
        return []

    # Group by location and count
    query = db.query(
        group_col,
        func.count(Photo.id).label('count')
    ).join(
        PhotoMetadata, Photo.id == PhotoMetadata.photo_id
    ).filter(
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
    covers = db.query(
        Photo,
        group_col
    ).join(
        PhotoMetadata, Photo.id == PhotoMetadata.photo_id
    ).filter(
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
    elif level == 'province':
        col = PhotoMetadata.province
    elif level == 'district':
        col = PhotoMetadata.district
    else:
        return []
        
    return db.query(Photo).join(
        PhotoMetadata, Photo.id == PhotoMetadata.photo_id
    ).filter(
        col == name
    ).order_by(
        desc(Photo.photo_time)
    ).offset(skip).limit(limit).all()

def get_location_distribution(db: Session, level: str = 'city'):
    if level == 'city':
        group_col = PhotoMetadata.city
    elif level == 'province':
        group_col = PhotoMetadata.province
    elif level == 'district':
        group_col = PhotoMetadata.district
    else:
        return []

    # Group by location and count, no limit
    results = db.query(
        group_col.label('name'),
        func.count(Photo.id).label('count')
    ).join(
        PhotoMetadata, Photo.id == PhotoMetadata.photo_id
    ).filter(
        group_col.is_not(None),
        group_col != ''
    ).group_by(
        group_col
    ).all()

    return [{"name": r.name, "count": r.count, "level": level} for r in results]
