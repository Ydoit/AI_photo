from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, cast, String
from app.db.models.album import Album
from app.db.models.photo import Photo
from app.db.models.photo_metadata import PhotoMetadata
from app.schemas import album as schemas
from datetime import datetime

# Album CRUD
def get_album(db: Session, album_id: UUID):
    return db.query(Album).filter(Album.id == album_id).first()

def get_albums(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Album).offset(skip).limit(limit).all()

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

# Photo CRUD
def get_photos(db: Session, album_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(Photo).join(Photo.albums).filter(Album.id == album_id).options(joinedload(Photo.albums)).offset(skip).limit(limit).all()

def get_all_photos(db: Session, skip: int = 0, limit: int = 100, 
                   year: Optional[str] = None, 
                   city: Optional[str] = None, 
                   tag: Optional[str] = None):
    query = db.query(Photo).options(joinedload(Photo.albums)).outerjoin(PhotoMetadata)
    
    if year:
        try:
            year_int = int(year)
            query = query.filter(extract('year', Photo.photo_time) == year_int) # changed upload_time to photo_time
        except ValueError:
            pass
            
    if city:
        query = query.filter(cast(PhotoMetadata.location, String).ilike(f"%{city}%"))
        
    if tag:
        query = query.filter(cast(PhotoMetadata.tags, String).ilike(f"%{tag}%"))
        
    return query.offset(skip).limit(limit).all()

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
        db.delete(db_photo)
        db.commit()
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
    elif action == 'remove_from_album' and album:
        for photo in photos:
            if album in photo.albums:
                photo.albums.remove(album)
                count += 1
    elif action == 'delete':
        # Handled by batch_delete_photos_db, but good to keep consistent interface
        pass
        
    db.commit()
    return count

def batch_delete_photos_db(db: Session, photo_ids: List[UUID]):
    photos = get_photos_by_ids(db, photo_ids)
    count = len(photos)
    for photo in photos:
        db.delete(photo)
    db.commit()
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