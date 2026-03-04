from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc
from datetime import datetime, date
from app.db.models.photo import Photo, FileType
from app.db.models.face import Face, FaceIdentity
from app.db.models.tag import PhotoTag, PhotoTagRelation
from app.schemas.dashboard import (
    DashboardCard, DashboardFace, DashboardFaceItem, 
    DashboardContentStats, ContentDetail, DashboardTime, 
    DashboardTimeChartItem, DashboardResponse
)

def get_dashboard_stats(db: Session, owner_id: UUID) -> DashboardResponse:
    # 1. Card Stats
    total_media = db.query(Photo).filter(Photo.owner_id == owner_id).count()
    
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_new = db.query(Photo).filter(Photo.upload_time >= today_start, Photo.owner_id == owner_id).count()
    
    total_size_bytes = db.query(func.sum(Photo.size)).filter(Photo.owner_id== owner_id).scalar() or 0
    # Convert bytes to GB
    storage_gb = total_size_bytes / (1024 * 1024 * 1024)
    storage_used = f"{storage_gb:.1f}GB"

    card = DashboardCard(
        total_media=total_media,
        today_new=today_new,
        storage_used=storage_used
    )

    # 2. Face Stats
    total_identified = db.query(FaceIdentity).filter(FaceIdentity.is_deleted == False, FaceIdentity.owner_id == owner_id).count()

    # Pending faces (faces without identity)
    # Assuming pending means face_identity_id is NULL
    pending_faces_count = db.query(Face).join(Photo, Face.photo_id == Photo.id).filter(Face.face_identity_id == None, Face.is_deleted == False, Photo.owner_id == owner_id).count()

    # Unidentified photos count (photos that contain at least one unidentified face)
    # This might be similar to pending_faces_count but counting distinct photos
    unidentified_photos_count = db.query(func.count(func.distinct(Face.photo_id))).join(Photo, Face.photo_id == Photo.id).filter(Face.face_identity_id == None, Face.is_deleted == False, Photo.owner_id == owner_id).scalar() or 0
    
    # Top 3 Faces
    top_faces_query = db.query(
        FaceIdentity.id,
        FaceIdentity.identity_name,
        func.count(Face.id).label('count')
    ).join(Face, Face.face_identity_id == FaceIdentity.id)\
    .filter(FaceIdentity.is_deleted == False, Face.is_deleted == False, FaceIdentity.owner_id == owner_id)\
    .group_by(FaceIdentity.id)\
    .order_by(desc('count'))\
    .limit(3).all()

    top_faces = []
    for f_id, f_name, f_count in top_faces_query:
        # Get a representative photo for avatar
        # We need to join Face and Photo to get a photo_id
        # Simple approach: query one face for this identity
        face_sample = db.query(Face).filter(Face.face_identity_id == f_id).first()
        avatar_url = f"/api/medias/{face_sample.photo_id}/thumbnail" if face_sample else None
        
        top_faces.append(DashboardFaceItem(
            id=str(f_id),
            name=f_name or "Unknown",
            count=f_count,
            avatar_url=avatar_url
        ))

    face_stats = DashboardFace(
        total_identified=total_identified,
        top_faces=top_faces,
        pending_faces_count=pending_faces_count, # Using simple count for now as per prompt "5位待确认" might need clustering logic which is complex
        unidentified_photos_count=unidentified_photos_count
    )

    # 3. Content Stats
    # Photos
    photos_count = db.query(Photo).filter(Photo.file_type == FileType.image, Photo.owner_id == owner_id).count()
    # Mock breakdown for photos
    photos_detail = ContentDetail(
        total=photos_count,
        sub_1_label="普通",
        sub_1_count=photos_count, # simplified
        sub_2_label="截图",
        sub_2_count=0 # simplified
    )

    # Videos
    videos_count = db.query(Photo).filter(Photo.file_type.in_([FileType.video, FileType.live_photo]), Photo.owner_id == owner_id).count()
    # Mock breakdown for videos
    videos_detail = ContentDetail(
        total=videos_count,
        sub_1_label="短视频",
        sub_1_count=videos_count,
        sub_2_label="长视频",
        sub_2_count=0
    )

    # Tags (Scenery, Food)
    # Need to check if tags exist. 
    scenery_count = db.query(PhotoTagRelation).join(PhotoTag).filter(PhotoTag.tag_name == '风景').count()
    food_count = db.query(PhotoTagRelation).join(PhotoTag).filter(PhotoTag.tag_name == '美食').count()

    content_stats = DashboardContentStats(
        photos=photos_detail,
        videos=videos_detail,
        scenery_count=scenery_count,
        food_count=food_count
    )

    # 4. Time Stats
    # Group by Year
    year_stats = db.query(
        func.extract('year', Photo.photo_time).label('year'),
        func.count(Photo.id).label('count')
    ).filter(Photo.owner_id == owner_id)\
    .group_by(func.extract('year', Photo.photo_time))\
    .order_by(desc('year')).all()

    chart_data = []
    colors = ['#4A90E2', '#67C23A', '#909399', '#E6A23C', '#F56C6C']
    
    total_for_chart = sum([item.count for item in year_stats]) if year_stats else 0
    current_year = datetime.now().year
    current_year_percentage = 0

    for i, (year, count) in enumerate(year_stats):
        if year is None: continue
        percentage = round((count / total_for_chart) * 100, 1) if total_for_chart > 0 else 0
        if int(year) == current_year:
            current_year_percentage = int(percentage)
        
        chart_data.append(DashboardTimeChartItem(
            year=int(year),
            count=count,
            percentage=percentage,
            color=colors[i % len(colors)]
        ))

    # Monthly Peak
    # Find month with max photos
    # Postgres specific: date_trunc or extract
    # We can group by year-month
    month_stats = db.query(
        func.extract('year', Photo.photo_time).label('year'),
        func.extract('month', Photo.photo_time).label('month'),
        func.count(Photo.id).label('count')
    ).filter(Photo.owner_id == owner_id)\
    .group_by(
        func.extract('year', Photo.photo_time),
        func.extract('month', Photo.photo_time)
    ).order_by(desc('count')).first()

    if month_stats:
        m_year = int(month_stats.year)
        m_month = int(month_stats.month)
        m_count = month_stats.count
        monthly_peak = f"{m_year}年{m_month}月拍摄最多：{m_count}张"
    else:
        monthly_peak = "暂无数据"

    time_stats = DashboardTime(
        current_year_percentage=current_year_percentage,
        chart_data=chart_data,
        monthly_peak=monthly_peak
    )

    return DashboardResponse(
        card=card,
        face=face_stats,
        content=content_stats,
        time=time_stats
    )
