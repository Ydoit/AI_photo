from typing import List, Optional
from uuid import UUID
import os

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, cast, String, func, and_, or_
from datetime import datetime

from app.db.models.album import Album
from app.db.models.photo import Photo
from app.db.models.photo_metadata import PhotoMetadata
from app.db.models.face import Face
from app.db.models.tag import PhotoTag
from app.db.models.image_vector import ImageVector
from app.schemas import album as album_schemas
from app.schemas import photo as photo_schemas
from app.schemas.metadata import PhotoMetadataUpdate,PhotoMetadataCreate
from app.service import storage
from app.crud import face as crud_face
from app.db.models.photo import FileType, ImageType
from app.utils.exif import extract_metadata

# Album CRUD
def _build_album_query(db: Session, album: Album):
    query = db.query(Photo)
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

def get_album(db: Session, album_id: UUID):
    return db.query(Album).options(joinedload(Album.cover)).filter(Album.id == album_id).first()

def get_albums_by_photo_id(db: Session, photo_id: UUID):
    return db.query(Album).join(Album.photos).filter(Photo.id == photo_id).all()

def get_albums(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Album).options(joinedload(Album.cover)).offset(skip).limit(limit).all()

def create_album(db: Session, album: album_schemas.AlbumCreate, query_embedding: Optional[List[float]] = None):
    db_album = Album(
        name=album.name, 
        description=album.description,
        type=album.type,
        condition=album.condition,
        query_embedding=query_embedding,
        threshold=album.threshold
    )
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

def update_album(db: Session, album_id: UUID, album: album_schemas.AlbumCreate, query_embedding: Optional[List[float]] = None):
    db_album = get_album(db, album_id)
    if db_album:
        db_album.name = album.name
        if album.description is not None:
            db_album.description = album.description
        if album.condition is not None:
            db_album.condition = album.condition
        if album.threshold is not None:
            db_album.threshold = album.threshold
        if query_embedding is not None:
            db_album.query_embedding = query_embedding

        db.commit()
        db.refresh(db_album)

        return db_album

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

    extracted_meta = extract_metadata(file_path, file_name, extract_location_details=False)

    # Create Schema for DB
    photo_create = photo_schemas.PhotoCreate(
        file_type=file_type,
        size=size,
        width=width,
        height=height,
        duration=duration,
        filename=file_name,
        photo_time=extracted_meta["photo_time"]
    )

    return create_photo(db, photo_create, album_id, file_path, photo_id=photo_id)


# Photo CRUD
def get_photos(db: Session, album_id: UUID, skip: int = 0, limit: int = 100, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
    # Retrieve album details first
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        return []

    query = _build_album_query(db, album)

    # Ordering
    if album.type == 'smart' and album.query_embedding is not None:
        # Order by similarity
        distance = ImageVector.embedding.cosine_distance(album.query_embedding)
        query = query.order_by(distance)
    else:
        # Default order by time
        query = query.order_by(Photo.photo_time.desc())
    
    # Common filters (start_time, end_time from args)
    if start_time:
        query = query.filter(Photo.photo_time >= start_time)
    if end_time:
        query = query.filter(Photo.photo_time <= end_time)

    # Optimization for user albums
    if album.type == 'user':
        query = query.options(joinedload(Photo.albums))

    if limit == 0:
        return query.offset(skip).all()
    return query.offset(skip).limit(limit).all()

def get_photos_by_time(db: Session, skip: int = 0, limit: int = 100, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
    query = db.query(Photo)
    if start_time:
        query = query.filter(Photo.photo_time >= start_time)
    if end_time:
        query = query.filter(Photo.photo_time <= end_time)
    # 按拍摄时间倒序
    query = query.order_by(Photo.photo_time.desc())
    if limit == 0:
        # 不限制数量，返回所有照片
        return query.offset(skip).all()
    return query.offset(skip).limit(limit).all()

def get_filter_options(db: Session):
    # Years
    years = db.query(func.extract('year', Photo.photo_time)).distinct().order_by(func.extract('year', Photo.photo_time).desc()).all()
    years = [int(y[0]) for y in years if y[0] is not None]

    # Cities
    cities = db.query(PhotoMetadata.city).distinct().filter(PhotoMetadata.city.isnot(None)).order_by(PhotoMetadata.city).all()
    cities = [c[0] for c in cities if c[0]]

    # Makes
    makes = db.query(PhotoMetadata.make).distinct().filter(PhotoMetadata.make.isnot(None)).order_by(PhotoMetadata.make).all()
    makes = [m[0] for m in makes if m[0]]

    # Models
    models = db.query(PhotoMetadata.model).distinct().filter(PhotoMetadata.model.isnot(None)).order_by(PhotoMetadata.model).all()
    models = [m[0] for m in models if m[0]]

    # Image Types
    image_types = [t.value for t in ImageType]
    
    # File Types
    file_types = [t.value for t in FileType]

    return {
        "years": years,
        "cities": cities,
        "makes": makes,
        "models": models,
        "image_types": image_types,
        "file_types": file_types
    }

def _build_photo_filter_query(
    db: Session,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    years: Optional[List[int]] = None,
    city: Optional[str] = None,
    cities: Optional[List[str]] = None,
    province: Optional[str] = None,
    country: Optional[str] = None,
    make: Optional[str] = None,
    makes: Optional[List[str]] = None,
    model: Optional[str] = None,
    models: Optional[List[str]] = None,
    image_type: Optional[str] = None,
    image_types: Optional[List[str]] = None,
    file_type: Optional[str] = None,
    file_types: Optional[List[str]] = None,
    tag: Optional[str] = None,
    album_id: Optional[UUID] = None,
    face_id: Optional[UUID] = None,
    tag_id: Optional[UUID] = None,
    lat_min: Optional[float] = None,
    lat_max: Optional[float] = None,
    lng_min: Optional[float] = None,
    lng_max: Optional[float] = None,
    radius: Optional[float] = None,
    center_lat: Optional[float] = None,
    center_lng: Optional[float] = None,
    ids: Optional[List[UUID]] = None
):
    # 先筛选 Photo，减少后续连表的数据量
    photo_query = db.query(Photo.id)

    # Filter by IDs if provided
    if ids:
        photo_query = photo_query.filter(Photo.id.in_(ids))

    # 时间范围过滤（Photo 表）
    if start_time or end_time:
        if not start_time:
            start_time = datetime.min
        if not end_time:
            end_time = datetime.max
        photo_query = photo_query.filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time)

    # Years Filter
    if years:
        photo_query = photo_query.filter(func.extract('year', Photo.photo_time).in_(years))

    # Image Types Filter
    if image_types:
        photo_query = photo_query.filter(Photo.image_type.in_(image_types))
    elif image_type:
        photo_query = photo_query.filter(Photo.image_type == image_type)

    # File Types Filter
    if file_types:
        photo_query = photo_query.filter(Photo.file_type.in_(file_types))
    elif file_type:
        photo_query = photo_query.filter(Photo.file_type == file_type)

    # 如果指定 album_id，先过滤出该相册下的 photo_id
    if album_id is not None:
        photo_query = photo_query.join(Photo.albums).filter(Album.id == album_id)

    # Face Identity Filter
    if face_id is not None:
        photo_query = photo_query.join(Photo.faces).filter(Face.face_identity_id == face_id)

    # Tag ID Filter
    if tag_id is not None:
        photo_query = photo_query.join(Photo.tags).filter(PhotoTag.id == tag_id)

    # Tag Name Filter (if tag string provided)
    if tag is not None and tag.strip():
        photo_query = photo_query.join(Photo.tags).filter(PhotoTag.tag_name.ilike(f"%{tag.strip()}%"))

    has_metadata_filters = (
        (city and city.strip()) or cities or
        province or country or
        (make and make.strip()) or makes or
        (model and model.strip()) or models or
        lat_min or lat_max or lng_min or lng_max or radius or center_lat or center_lng
    )

    if has_metadata_filters:
        # 得到候选 photo_id 子查询
        photo_subquery = photo_query.subquery()

        # 主查询：仅对候选照片做连表与剩余过滤
        query = (
            db.query(Photo)
            .join(photo_subquery, Photo.id == photo_subquery.c.id)
            .outerjoin(PhotoMetadata)
        )

        # 地理位置与标签过滤（PhotoMetadata 表）
        if cities:
            query = query.filter(PhotoMetadata.city.in_(cities))
        elif city is not None and city.strip():
            query = query.filter(PhotoMetadata.city.ilike(f"%{city.strip()}%"))
        
        if province:
            query = query.filter(PhotoMetadata.province.ilike(f"%{province.strip()}%"))
        if country:
            query = query.filter(PhotoMetadata.country.ilike(f"%{country.strip()}%"))

        # Camera Make/Model Filters
        if makes:
            query = query.filter(PhotoMetadata.make.in_(makes))
        elif make and make.strip():
            query = query.filter(PhotoMetadata.make.ilike(f"%{make.strip()}%"))
        
        if models:
            query = query.filter(PhotoMetadata.model.in_(models))
        elif model and model.strip():
            query = query.filter(PhotoMetadata.model.ilike(f"%{model.strip()}%"))

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
        
        return query
    else:
        # 得到候选 photo_id 子查询
        photo_subquery = photo_query.subquery()

        # 主查询：仅对候选照片做连表与剩余过滤
        query = (
            db.query(Photo)
            .join(photo_subquery, Photo.id == photo_subquery.c.id)
        )
        return query

def get_all_photos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    years: Optional[List[int]] = None,
    city: Optional[str] = None,
    cities: Optional[List[str]] = None,
    province: Optional[str] = None,
    country: Optional[str] = None,
    make: Optional[str] = None,
    makes: Optional[List[str]] = None,
    model: Optional[str] = None,
    models: Optional[List[str]] = None,
    image_type: Optional[str] = None,
    image_types: Optional[List[str]] = None,
    file_type: Optional[str] = None,
    file_types: Optional[List[str]] = None,
    tag: Optional[str] = None,
    album_id: Optional[UUID] = None,
    face_id: Optional[UUID] = None,
    tag_id: Optional[UUID] = None,
    lat_min: Optional[float] = None,
    lat_max: Optional[float] = None,
    lng_min: Optional[float] = None,
    lng_max: Optional[float] = None,
    radius: Optional[float] = None,
    center_lat: Optional[float] = None,
    center_lng: Optional[float] = None,
    ids: Optional[List[UUID]] = None
):
    query = _build_photo_filter_query(
        db, start_time, end_time, years, city, cities, province, country,
        make, makes, model, models, image_type, image_types, file_type, file_types,
        tag, album_id, face_id, tag_id, lat_min, lat_max, lng_min, lng_max,
        radius, center_lat, center_lng, ids
    )

    # Optimization for user albums / eager load albums
    query = query.options(joinedload(Photo.albums))

    # 按拍摄时间倒序
    query = query.order_by(Photo.photo_time.desc())
    return query.offset(skip).limit(limit).all()

def get_timeline_stats(
    db: Session,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    years: Optional[List[int]] = None,
    city: Optional[str] = None,
    cities: Optional[List[str]] = None,
    province: Optional[str] = None,
    country: Optional[str] = None,
    make: Optional[str] = None,
    makes: Optional[List[str]] = None,
    model: Optional[str] = None,
    models: Optional[List[str]] = None,
    image_type: Optional[str] = None,
    image_types: Optional[List[str]] = None,
    file_type: Optional[str] = None,
    file_types: Optional[List[str]] = None,
    tag: Optional[str] = None,
    album_id: Optional[UUID] = None,
    face_id: Optional[UUID] = None,
    tag_id: Optional[UUID] = None,
    lat_min: Optional[float] = None,
    lat_max: Optional[float] = None,
    lng_min: Optional[float] = None,
    lng_max: Optional[float] = None,
    radius: Optional[float] = None,
    center_lat: Optional[float] = None,
    center_lng: Optional[float] = None,
    ids: Optional[List[UUID]] = None
):
    query = _build_photo_filter_query(
        db, start_time, end_time, years, city, cities, province, country,
        make, makes, model, models, image_type, image_types, file_type, file_types,
        tag, album_id, face_id, tag_id, lat_min, lat_max, lng_min, lng_max,
        radius, center_lat, center_lng, ids
    )
    
    # 总数
    total = query.count()

    if total == 0:
        return {
            'total_photos': 0,
            'time_range': None,
            'timeline': []
        }

    # 按年-月-日分组
    # 使用 extract 保证跨数据库兼容性
    timeline_query = query.with_entities(
        func.extract('year', Photo.photo_time).label('year'),
        func.extract('month', Photo.photo_time).label('month'),
        func.extract('day', Photo.photo_time).label('day'),
        func.count(Photo.id).label('count')
    ).group_by(
        func.extract('year', Photo.photo_time),
        func.extract('month', Photo.photo_time),
        func.extract('day', Photo.photo_time)
    ).order_by(
        func.extract('year', Photo.photo_time).desc(),
        func.extract('month', Photo.photo_time).desc(),
        func.extract('day', Photo.photo_time).desc()
    ).all()

    timeline = []
    min_time = None
    max_time = None
    for y, m, d, c in timeline_query:
        if y is not None and m is not None and d is not None:
            timeline.append({
                'year': int(y),
                'month': int(m),
                'day': int(d),
                'count': c
            })
            dt = datetime(int(y), int(m), int(d))
            if min_time is None or dt < min_time:
                min_time = dt
            if max_time is None or dt > max_time:
                max_time = dt

    return {
        'total_photos': total,
        'time_range': {
            'start': min_time.isoformat() if min_time else None,
            'end': max_time.isoformat() if max_time else None
        },
        'timeline': timeline
    }

def get_photo(db: Session, photo_id: UUID):
    return db.query(Photo).filter(Photo.id == photo_id).first()

def create_photo(db: Session, photo: photo_schemas.PhotoCreate, album_id: Optional[UUID], file_path: str, photo_id: Optional[UUID] = None):
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

    if album_id:
        album = get_album(db, album_id)
        if album:
            db_photo.albums.append(album)
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)

    if album_id:
        _update_album_photo_count(db, album_id)

    db.commit()

    return db_photo

def update_photo(db: Session, photo_id: UUID, photo_update: photo_schemas.PhotoUpdate):
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
    photos = (
        db.query(Photo)
        .options(joinedload(Photo.albums))
        .filter(Photo.id.in_(photo_ids))
        .all()
    )
    if not photos:
        return 0

    album = None
    if album_id:
        album = get_album(db, album_id)
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

def batch_delete_photos_db(db: Session, photo_ids: List[UUID]):
    # Get photos with albums to know which albums to update
    photos = db.query(Photo).options(joinedload(Photo.albums), joinedload(Photo.faces)).filter(Photo.id.in_(photo_ids)).all()
    affected_album_ids = set()
    for photo in photos:
        for album in photo.albums:
            affected_album_ids.add(album.id)
        
        # Handle face deletion dependencies
        for face in photo.faces:
            crud_face.handle_face_deletion_dependency(db, face)

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

def update_photo_metadata(db: Session, photo_id: UUID, metadata: PhotoMetadataUpdate):
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
    - photo: album_schemas.PhotoCreate
    - album_id: Optional[UUID]
    - file_path: str
    - photo_id: UUID
    """
    if not photos_data:
        return 0

    db_photos = []

    for item in photos_data:
        photo = item['photo']
        file_path = item['file_path']
        photo_id = item['photo_id']
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

    try:
        db.add_all(db_photos)
        db.commit()
        return len(db_photos)
    except Exception as e:
        db.rollback()
        raise e