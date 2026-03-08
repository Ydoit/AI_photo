from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from datetime import datetime

from app.db.models.album import Album
from app.db.models.photo import Photo
from app.db.models.photo_metadata import PhotoMetadata
from app.db.models.face import Face
from app.db.models.image_vector import ImageVector
from app.db.models.user import User
from app.schemas import album as album_schemas


# Album CRUD
def _build_album_query(db: Session, album: Album):
    query = db.query(Photo)
    
    # Ensure smart/conditional albums only see user's own photos
    if album.owner_id is not None:
        query = query.filter(Photo.owner_id == album.owner_id)

    if album.type == 'conditional' and album.condition:
        query = query.outerjoin(PhotoMetadata)
        cond = album.condition
        # Time Range
        if 'time_range' in cond:
            tr = cond['time_range']
            if tr.get('start'):
                try:
                    s = datetime.fromisoformat(tr['start'].replace('Z', '+00:00'))
                    query = query.filter(Photo.photo_time >= s)
                except:
                    pass
            if tr.get('end'):
                try:
                    e = datetime.fromisoformat(tr['end'].replace('Z', '+00:00'))
                    query = query.filter(Photo.photo_time <= e)
                except:
                    pass
        # Location
        if 'locations' in cond and isinstance(cond['locations'], list) and cond['locations']:
             loc_filters = []
             for loc in cond['locations']:
                 sub_filters = []
                 if loc.get('province'):
                     sub_filters.append(PhotoMetadata.province == loc['province'])
                 if loc.get('city'):
                     sub_filters.append(PhotoMetadata.city == loc['city'])
                 if loc.get('district'):
                     sub_filters.append(PhotoMetadata.district == loc['district'])
                 if sub_filters:
                     loc_filters.append(and_(*sub_filters))
             if loc_filters:
                 query = query.filter(or_(*loc_filters))

        # People
        if 'people' in cond and isinstance(cond['people'], list) and cond['people']:
             people_ids = cond['people']
             # Assuming people_ids are UUID strings
             query = query.join(Photo.faces).filter(Face.face_identity_id.in_(people_ids))

        # Deduplicate
        query = query.group_by(Photo.id)

    elif album.type == 'smart' and album.query_embedding is not None:
        # Vector Search
        query = query.join(ImageVector)
        
        # Cosine distance
        distance = ImageVector.embedding.cosine_distance(album.query_embedding)
        
        # Threshold Logic
        # user_threshold is similarity (0-1), where 1 is identical.
        # cosine_distance is distance (0-2), where 0 is identical.
        # distance = 1 - similarity (approx, for normalized vectors)
        # So: similarity > threshold  =>  (1 - distance) > threshold  =>  distance < (1 - threshold)
        
        user_threshold = album.threshold if album.threshold is not None else 0.25
        dist_threshold = 1.0 - user_threshold

        # Clamp distance threshold to avoid logical errors
        dist_threshold = max(0.0, min(1.0, dist_threshold))

        query = query.filter(distance < dist_threshold)

    else:
        # Standard User Album
        query = query.join(Photo.albums).filter(Album.id == album.id)
    
    return query

def _update_album_photo_count(db: Session, album_id: UUID):
    album = db.query(Album).filter(Album.id == album_id).first()
    if album:
        query = _build_album_query(db, album)
        count = query.count()
        album.num_photos = count
        db.add(album)
        db.commit()

def get_album(db: Session, album_id: UUID, user_id: UUID = None):
    query = db.query(Album).options(joinedload(Album.cover)).filter(Album.id == album_id)
    if user_id is not None:
        query = query.filter(or_(Album.owner_id == user_id, Album.shared_users.any(id=user_id)))
    return query.first()

def get_albums_by_photo_id(db: Session, photo_id: UUID):
    return db.query(Album).join(Album.photos).filter(Photo.id == photo_id).all()

def get_albums(db: Session, skip: int = 0, limit: int = 100, user_id: UUID = None):
    query = db.query(Album).options(joinedload(Album.cover))
    if user_id is not None:
        query = query.filter(or_(Album.owner_id == user_id, Album.shared_users.any(id=user_id)))
    return query.offset(skip).limit(limit).all()

def create_album(db: Session, album: album_schemas.AlbumCreate, query_embedding: Optional[List[float]] = None, user_id: UUID = None):
    db_album = Album(
        name=album.name, 
        description=album.description,
        type=album.type,
        condition=album.condition,
        query_embedding=query_embedding,
        threshold=album.threshold,
        owner_id=user_id
    )
    
    if album.shared_users:
        users = db.query(User).filter(User.id.in_(album.shared_users)).all()
        db_album.shared_users = users

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

def update_album(db: Session, album_id: UUID, album: Union[album_schemas.AlbumUpdate, album_schemas.AlbumCreate], query_embedding: Optional[List[float]] = None):
    db_album = get_album(db, album_id)
    if db_album:
        if album.name:
            db_album.name = album.name
        if album.description is not None:
            db_album.description = album.description
        if album.condition is not None:
            db_album.condition = album.condition
        if album.threshold is not None:
            db_album.threshold = album.threshold
        if query_embedding is not None:
            db_album.query_embedding = query_embedding

        # Handle shared_users
        shared_users_ids = getattr(album, 'shared_users', None)
        if shared_users_ids is not None:
            if not shared_users_ids:
                db_album.shared_users = []
            else:
                users = db.query(User).filter(User.id.in_(shared_users_ids)).all()
                db_album.shared_users = users

        db.commit()
        db.refresh(db_album)

        return db_album

    return db_album


# Photo CRUD

def batch_update_album_association(db: Session, photo_ids: List[UUID], album_id: UUID, action: str, user_id: UUID = None):
    """
    批量更新照片与相册的关联关系，支持添加、移除或删除操作。
    优化点：
    1. 使用 joinedload 预加载 albums，避免 N+1 查询
    2. 使用集合操作批量处理关联关系，减少逐条判断
    3. 仅在必要时更新相册封面
    4. 使用 bulk 操作减少 commit 次数
    """
    if not photo_ids:
        return 0

    # 预加载照片及其关联的相册，避免后续 N+1 查询
    query = (
        db.query(Photo)
        .options(joinedload(Photo.albums))
        .filter(Photo.id.in_(photo_ids))
    )
    if user_id is not None:
        query = query.filter(Photo.owner_id == user_id)
        
    photos = query.all()
    if not photos:
        return 0

    album = None
    if album_id:
        album = get_album(db, album_id, user_id=user_id)
        if not album:
            return 0

    count = 0

    if action == 'add_to_album' and album:
        # 使用集合差集快速找出未关联的照片
        photos_to_add = [p for p in photos if album not in p.albums]
        for photo in photos_to_add:
            photo.albums.append(album)
        count = len(photos_to_add)
        # 仅在相册无封面且新增照片时设置封面
        if not album.cover_id and photos_to_add:
            album.cover_id = photos_to_add[0].id
            db.add(album)

    elif action == 'remove_from_album' and album:
        # 使用集合交集快速找出已关联的照片
        photos_to_remove = [p for p in photos if album in p.albums]
        for photo in photos_to_remove:
            photo.albums.remove(album)
        count = len(photos_to_remove)

    elif action == 'delete':
        # 由 batch_delete_photos_db 处理，此处仅保持一致接口
        pass

    # 批量提交所有变更
    if count > 0:
        db.add_all(photos)  # 确保关联变更被追踪
        db.commit()
        if album_id:
            _update_album_photo_count(db, album_id)

    return count

# Metadata CRUD

