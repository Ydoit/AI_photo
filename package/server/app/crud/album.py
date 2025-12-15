from typing import List, Optional
from uuid import UUID
import os

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, cast, String, func
from datetime import datetime

from app.db.models.album import Album
from app.db.models.photo import Photo
from app.db.models.photo_metadata import PhotoMetadata
from app.schemas import album as schemas
from app.service import storage
from app.db.models.photo import FileType
from app.utils.exif import extract_metadata

# Album CRUD
def _update_album_photo_count(db: Session, album_id: UUID):
    album = db.query(Album).filter(Album.id == album_id).first()
    if album:
        count = db.query(Photo).join(Photo.albums).filter(Album.id == album_id).count()
        album.num_photos = count
        db.add(album)
        db.commit()

def get_album(db: Session, album_id: UUID):
    return db.query(Album).options(joinedload(Album.cover)).filter(Album.id == album_id).first()

def get_albums(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Album).options(joinedload(Album.cover)).offset(skip).limit(limit).all()

def create_album(db: Session, album: schemas.AlbumCreate):
    db_album = Album(name=album.name, description=album.description)
    db.add(db_album)
    db.commit()
    db.refresh(db_album)
    return db_album

def delete_album(db: Session, album_id: UUID):
    db_album = get_album(db, album_id)
    if db_album:
        db.delete(db_album)
        db.commit()
    return db_album

def update_album(db: Session, album_id: UUID, album: schemas.AlbumCreate):
    db_album = get_album(db, album_id)
    if db_album:
        db_album.name = album.name
        if album.description is not None:
            db_album.description = album.description
        db.commit()
        db.refresh(db_album)
    return db_album


def save_and_create_photo(db: Session, file_path: str, file_name: str, album_id: Optional[UUID], photo_id: UUID):
    # Determine file type
    ext = os.path.splitext(file_name)[1]
    file_type = FileType.image
    if ext.lower() in ['.mp4', '.mov', '.avi']:
        file_type = FileType.video

    storage.generate_thumbnail(file_path, photo_id, db)

    # Get Metadata
    size = storage.get_file_size(file_path)
    width, height, duration = storage.get_image_dimensions(file_path)

    extracted_meta = extract_metadata(file_path, file_name)

    # Create Schema for DB
    photo_create = schemas.PhotoCreate(
        file_type=file_type,
        size=size,
        width=width,
        height=height,
        duration=duration,
        filename=file_name,
        photo_time=extracted_meta["photo_time"]
    )

    # Create Metadata Schema
    loc_details = extracted_meta.get("location_details", {})
    metadata_create = schemas.PhotoMetadataCreate(
        exif_info=extracted_meta["exif_info"],
        location=extracted_meta["location"],
        longitude=loc_details.get("longitude"),
        latitude=loc_details.get("latitude"),
        city=loc_details.get("city"),
        province=loc_details.get("province"),
        country=loc_details.get("country"),
        address=loc_details.get("address")
    )

    return create_photo(db, photo_create, album_id, file_path, photo_id=photo_id, metadata=metadata_create)


# Photo CRUD
def get_photos(db: Session, album_id: UUID, skip: int = 0, limit: int = 100, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
    query = db.query(Photo).join(Photo.albums).filter(Album.id == album_id).options(joinedload(Photo.albums))

    if start_time:
        query = query.filter(Photo.photo_time >= start_time)
    
    if end_time:
        query = query.filter(Photo.photo_time <= end_time)

    # 按拍摄时间倒序
    query = query.order_by(Photo.photo_time.desc())

    total = query.count()

    if limit == 0:
        # 不限制数量，返回所有照片
        return query.offset(skip).all(), total
    return query.offset(skip).limit(limit).all(), total

def get_all_photos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    city: Optional[str] = None,
    province: Optional[str] = None,
    country: Optional[str] = None,
    tag: Optional[str] = None,
    album_id: Optional[UUID] = None,
    lat_min: Optional[float] = None,
    lat_max: Optional[float] = None,
    lng_min: Optional[float] = None,
    lng_max: Optional[float] = None,
    radius: Optional[float] = None,
    center_lat: Optional[float] = None,
    center_lng: Optional[float] = None
):
    # 先筛选 Photo，减少后续连表的数据量
    photo_query = db.query(Photo.id).distinct()

    # 时间范围过滤（Photo 表）
    if start_time:
        photo_query = photo_query.filter(Photo.photo_time >= start_time)
    if end_time:
        photo_query = photo_query.filter(Photo.photo_time <= end_time)

    # 如果指定 album_id，先过滤出该相册下的 photo_id
    if album_id is not None:
        photo_query = photo_query.join(Photo.albums).filter(Album.id == album_id)

    # 得到候选 photo_id 子查询
    photo_subquery = photo_query.subquery()

    # 主查询：仅对候选照片做连表与剩余过滤
    query = (
        db.query(Photo)
        .join(photo_subquery, Photo.id == photo_subquery.c.id)
        .options(joinedload(Photo.albums))
        .outerjoin(PhotoMetadata)
    )

    # 地理位置与标签过滤（PhotoMetadata 表）
    if city is not None and city.strip():
        query = query.filter(PhotoMetadata.city.ilike(f"%{city.strip()}%"))
    if province:
        query = query.filter(PhotoMetadata.province.ilike(f"%{province.strip()}%"))
    if country:
        query = query.filter(PhotoMetadata.country.ilike(f"%{country.strip()}%"))

    if lat_min is not None:
        query = query.filter(PhotoMetadata.latitude >= lat_min)
    if lat_max is not None:
        query = query.filter(PhotoMetadata.latitude <= lat_max)
    if lng_min is not None:
        query = query.filter(PhotoMetadata.longitude >= lng_min)
    if lng_max is not None:
        query = query.filter(PhotoMetadata.longitude <= lng_max)

    if radius is not None and center_lat is not None and center_lng is not None:
        distance_expr = 6371 * func.acos(
            func.cos(func.radians(PhotoMetadata.latitude)) *
            func.cos(func.radians(center_lat)) *
            func.cos(func.radians(PhotoMetadata.longitude) - func.radians(center_lng)) +
            func.sin(func.radians(PhotoMetadata.latitude)) *
            func.sin(func.radians(center_lat))
        )
        query = query.filter(distance_expr <= radius)

    if tag is not None and tag.strip():
        query = query.filter(cast(PhotoMetadata.tags, String).ilike(f"%{tag.strip()}%"))

    # 按拍摄时间倒序
    query = query.order_by(Photo.photo_time.desc())
    
    total = query.count()
    
    return query.offset(skip).limit(limit).all(), total

def get_photo(db: Session, photo_id: UUID):
    return db.query(Photo).options(joinedload(Photo.albums)).filter(Photo.id == photo_id).first()

def create_photo(db: Session, photo: schemas.PhotoCreate, album_id: Optional[UUID], file_path: str, photo_id: Optional[UUID] = None, metadata: Optional[schemas.PhotoMetadataCreate] = None):
    db_photo = Photo(
        id=photo_id,
        # album_id removed
        file_path=file_path,
        file_type=photo.file_type,
        size=photo.size,
        width=photo.width,
        height=photo.height,
        duration=photo.duration,
        filename=photo.filename,
        photo_time=photo.photo_time or datetime.now()
    )
    
    if album_id:
        album = get_album(db, album_id)
        if album:
            db_photo.albums.append(album)
            
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    
    if album_id:
        _update_album_photo_count(db, album_id)
    
    # Initialize metadata
    db_metadata = PhotoMetadata(photo_id=db_photo.id)
    if metadata:
        if metadata.exif_info:
            db_metadata.exif_info = metadata.exif_info
        if metadata.location:
            db_metadata.location = metadata.location
        if metadata.location_api:
            db_metadata.location_api = metadata.location_api
        if metadata.tags:
            db_metadata.tags = metadata.tags
        if metadata.faces:
            db_metadata.faces = metadata.faces
            
        # Enhanced location fields
        if metadata.longitude is not None:
            db_metadata.longitude = metadata.longitude
        if metadata.latitude is not None:
            db_metadata.latitude = metadata.latitude
        if metadata.city:
            db_metadata.city = metadata.city
        if metadata.province:
            db_metadata.province = metadata.province
        if metadata.country:
            db_metadata.country = metadata.country
        if metadata.address:
            db_metadata.address = metadata.address

    db.add(db_metadata)
    db.commit()
    
    return db_photo

def update_photo(db: Session, photo_id: UUID, photo_update: schemas.PhotoUpdate):
    db_photo = get_photo(db, photo_id)
    if db_photo:
        if photo_update.filename is not None:
            db_photo.filename = photo_update.filename
        if photo_update.photo_time is not None:
            db_photo.photo_time = photo_update.photo_time
        db.commit()
        db.refresh(db_photo)
    return db_photo

def delete_photo(db: Session, photo_id: UUID):
    db_photo = get_photo(db, photo_id)
    if db_photo:
        affected_album_ids = [album.id for album in db_photo.albums]
        db.delete(db_photo)
        db.commit()
        for album_id in affected_album_ids:
            _update_album_photo_count(db, album_id)
    return db_photo

def get_photos_by_ids(db: Session, photo_ids: List[UUID]):
    return db.query(Photo).filter(Photo.id.in_(photo_ids)).all()

def batch_update_album_association(db: Session, photo_ids: List[UUID], album_id: UUID, action: str):
    photos = get_photos_by_ids(db, photo_ids)
    album = get_album(db, album_id) if album_id else None
    if not photos:
        return 0

    count = 0
    if action == 'add_to_album' and album:
        for photo in photos:
            if album not in photo.albums:
                photo.albums.append(album)
                count += 1
        if not album.cover_id and count > 0:
            album.cover_id = photos[0].id
    elif action == 'remove_from_album' and album:
        for photo in photos:
            if album in photo.albums:
                photo.albums.remove(album)
                count += 1
    elif action == 'delete':
        # Handled by batch_delete_photos_db, but good to keep consistent interface
        pass
        
    db.commit()

    if album_id and count > 0:
        _update_album_photo_count(db, album_id)

    return count

def batch_delete_photos_db(db: Session, photo_ids: List[UUID]):
    # Get photos with albums to know which albums to update
    photos = db.query(Photo).options(joinedload(Photo.albums)).filter(Photo.id.in_(photo_ids)).all()
    affected_album_ids = set()
    for photo in photos:
        for album in photo.albums:
            affected_album_ids.add(album.id)

    count = len(photos)
    for photo in photos:
        db.delete(photo)
    db.commit()
    
    # Update counts
    for album_id in affected_album_ids:
        _update_album_photo_count(db, album_id)
        
    return count

# Metadata CRUD
def get_photo_metadata(db: Session, photo_id: UUID):
    return db.query(PhotoMetadata).filter(PhotoMetadata.photo_id == photo_id).first()

def update_photo_metadata(db: Session, photo_id: UUID, metadata: schemas.PhotoMetadataUpdate):
    db_metadata = get_photo_metadata(db, photo_id)
    if not db_metadata:
        db_metadata = PhotoMetadata(photo_id=photo_id)
        db.add(db_metadata)
    
    update_data = metadata.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_metadata, key, value)
    
    db.add(db_metadata)
    db.commit()
    db.refresh(db_metadata)
    return db_metadata

def batch_create_photos(db: Session, photos_data: List[dict]):
    """
    Batch create photos.
    photos_data list of dict with keys:
    - photo: schemas.PhotoCreate
    - album_id: Optional[UUID]
    - file_path: str
    - photo_id: UUID
    - metadata: Optional[schemas.PhotoMetadataCreate]
    """
    if not photos_data:
        return 0

    db_photos = []
    db_metadatas = []
    
    for item in photos_data:
        photo = item['photo']
        file_path = item['file_path']
        photo_id = item['photo_id']
        metadata = item.get('metadata')
        
        db_photo = Photo(
            id=photo_id,
            file_path=file_path,
            file_type=photo.file_type,
            size=photo.size,
            width=photo.width,
            height=photo.height,
            duration=photo.duration,
            filename=photo.filename,
            photo_time=photo.photo_time or datetime.now()
        )
        # Skipping album association for batch insert as it's typically for scanning
        
        db_photos.append(db_photo)
        
        db_metadata = PhotoMetadata(photo_id=photo_id)
        if metadata:
            if metadata.exif_info:
                db_metadata.exif_info = metadata.exif_info
            if metadata.location:
                db_metadata.location = metadata.location
            if metadata.location_api:
                db_metadata.location_api = metadata.location_api
            if metadata.tags:
                db_metadata.tags = metadata.tags
            if metadata.faces:
                db_metadata.faces = metadata.faces
        db_metadatas.append(db_metadata)
        
    try:
        db.add_all(db_photos)
        db.add_all(db_metadatas)
        db.commit()
        return len(db_photos)
    except Exception as e:
        db.rollback()
        raise e