from typing import List, Optional
from datetime import datetime
import random
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc, and_

from app.dependencies import get_db
from app.db.models.photo import Photo
from app.db.models.photo_metadata import PhotoMetadata
from app.db.models.face import Face, FaceIdentity
from app.db.models.tag import PhotoTag, PhotoTagRelation
from app.schemas.annual_report import (
    AnnualReportData, UserInfo, TimeMetrics, MemoryMetrics, 
    EmotionMetrics, LocationMetrics, SeasonMetrics, SeasonData,
    EasterEgg, EasterEggTags, CategoryDistributionItem, TopCity,
    LocationPoint, CarouselGroup
)

router = APIRouter()

@router.get("", response_model=AnnualReportData)
def get_annual_report(
    year: int = Query(default=datetime.now().year, description="Report Year"),
    db: Session = Depends(get_db)
):
    # Base query for the year
    base_query = db.query(Photo).filter(extract('year', Photo.photo_time) == year)
    total_photos = base_query.count()

    # --- Time Metrics ---
    # Accompany Days (distinct dates)
    # Note: SQLite/Postgres compatibility for date extraction might differ, assuming Postgres or standard SQL
    accompany_days = base_query.with_entities(func.date(Photo.photo_time)).distinct().count()

    # First/Last Photo
    first_photo = base_query.order_by(Photo.photo_time.asc()).first()
    last_photo = base_query.order_by(Photo.photo_time.desc()).first()

    # Late Night Photos (00:00 - 05:00)
    late_night_count = base_query.filter(extract('hour', Photo.photo_time) < 5).count()

    time_metrics = TimeMetrics(
        totalPhotos=total_photos,
        accompanyDays=accompany_days,
        firstPhotoDate=first_photo.photo_time.strftime('%Y-%m-%d') if first_photo else None,
        lastPhotoDate=last_photo.photo_time.strftime('%Y-%m-%d') if last_photo else None,
        lateNightPhotoCount=late_night_count
    )

    # --- Memory Metrics ---
    # Category Distribution (Top Tags)
    # Join Photo -> PhotoTagRelation -> PhotoTag
    top_tags = db.query(PhotoTag.tag_name, func.count(PhotoTagRelation.photo_id).label('count'))\
        .join(PhotoTagRelation, PhotoTag.id == PhotoTagRelation.tag_id)\
        .join(Photo, Photo.id == PhotoTagRelation.photo_id)\
        .filter(extract('year', Photo.photo_time) == year)\
        .group_by(PhotoTag.tag_name)\
        .order_by(desc('count'))\
        .limit(5).all()

    category_distribution = [CategoryDistributionItem(name=t[0], value=t[1]) for t in top_tags]
    if not category_distribution:
        # Fallback if no tags
        category_distribution = [CategoryDistributionItem(name="生活日常", value=total_photos)]

    # Top Person
    top_person = db.query(FaceIdentity.identity_name, func.count(Face.id).label('count'))\
        .join(Face, Face.face_identity_id == FaceIdentity.id)\
        .join(Photo, Photo.id == Face.photo_id)\
        .filter(extract('year', Photo.photo_time) == year)\
        .group_by(FaceIdentity.identity_name)\
        .order_by(desc('count')).first()

    top_person_count = top_person[1] if top_person else 0
    # TODO: Identify Top Person Name properly

    # Top Location
    top_location_row = db.query(PhotoMetadata.city, func.count(Photo.id).label('count'))\
        .join(Photo, Photo.id == PhotoMetadata.photo_id)\
        .filter(extract('year', Photo.photo_time) == year)\
        .filter(PhotoMetadata.city.isnot(None))\
        .group_by(PhotoMetadata.city)\
        .order_by(desc('count')).first()

    top_location = top_location_row[0] if top_location_row else "未知"

    # Max Photo Day
    max_photo_day_row = base_query.with_entities(
            func.date(Photo.photo_time).label('date'), 
            func.count(Photo.id).label('count')
        )\
        .group_by('date')\
        .order_by(desc('count')).first()

    max_photo_day = str(max_photo_day_row[0]) if max_photo_day_row else "2024-01-01"
    max_photo_day_count = max_photo_day_row[1] if max_photo_day_row else 0

    memory_metrics = MemoryMetrics(
        categoryDistribution=category_distribution,
        topPersonCount=top_person_count,
        topLocation=top_location,
        maxPhotoDay=max_photo_day,
        maxPhotoDayCount=max_photo_day_count,
        topFeature="实况模式", # TODO: Implement feature detection
        topFeatureCount=int(total_photos * 0.3) # Mock
    )

    # --- Location Metrics ---
    # Lighten Province/City
    lighten_province = db.query(func.count(func.distinct(PhotoMetadata.province)))\
        .join(Photo, Photo.id == PhotoMetadata.photo_id)\
        .filter(extract('year', Photo.photo_time) == year).scalar()

    lighten_city = db.query(func.count(func.distinct(PhotoMetadata.city)))\
        .join(Photo, Photo.id == PhotoMetadata.photo_id)\
        .filter(extract('year', Photo.photo_time) == year).scalar()

    # Top Cities
    top_cities_rows = db.query(PhotoMetadata.city, PhotoMetadata.province, func.count(Photo.id).label('count'))\
        .join(Photo, Photo.id == PhotoMetadata.photo_id)\
        .filter(extract('year', Photo.photo_time) == year)\
        .filter(PhotoMetadata.city.isnot(None))\
        .group_by(PhotoMetadata.city, PhotoMetadata.province)\
        .order_by(desc('count'))\
        .limit(3).all()

    top_cities = [TopCity(cityName=row[0], provinceName=row[1] or "", photoCount=row[2]) for row in top_cities_rows]

    # Location Points (Aggregated by City for Map Display)
    points_rows = db.query(
        func.max(PhotoMetadata.longitude),
        func.max(PhotoMetadata.latitude),
        PhotoMetadata.city,
        func.count(Photo.id)
    )\
    .join(Photo, Photo.id == PhotoMetadata.photo_id)\
    .filter(extract('year', Photo.photo_time) == year)\
    .filter(PhotoMetadata.city.isnot(None))\
    .filter(PhotoMetadata.longitude.isnot(None))\
    .group_by(PhotoMetadata.city)\
    .order_by(desc(func.count(Photo.id)))\
    .limit(50).all()

    location_points = []
    for row in points_rows:
        lng, lat, city, count = row
        if not city:
            continue
            
        # Get representative photo for cover
        cover_photo = db.query(Photo).join(PhotoMetadata)\
            .filter(extract('year', Photo.photo_time) == year)\
            .filter(PhotoMetadata.city == city)\
            .first()
            
        cover_url = f"/api/medias/{cover_photo.id}/thumbnail" if cover_photo else None

        location_points.append(
            LocationPoint(
                lng=float(lng), 
                lat=float(lat), 
                name=city, 
                count=count,
                coverUrl=cover_url
            )
        )

    location_metrics = LocationMetrics(
        lightenProvinceNum=lighten_province or 0,
        lightenCityNum=lighten_city or 0,
        topCities=top_cities,
        locationPoints=location_points
    )

    # --- Season Metrics ---
    seasons_def = [
        ("春", [3, 4, 5], "嫩芽"),
        ("夏", [6, 7, 8], "蝉鸣"),
        ("秋", [9, 10, 11], "晚风"),
        ("冬", [12, 1, 2], "暖意")
    ]
    season_list = []
    
    for name, months, default_tag in seasons_def:
        # Filter photos in these months
        season_query = base_query.filter(extract('month', Photo.photo_time).in_(months))
        count = season_query.count()
        
        # Get one representative photo (e.g., random or first)
        rep_photo = season_query.first()
        # TODO: Replace with real URL generation logic
        rep_photo_url = f"/api/medias/{rep_photo.id}/thumbnail" if rep_photo else f"https://picsum.photos/seed/{name}/400/600"

        season_list.append(SeasonData(
            seasonName=name,
            photoCount=count,
            topTag=default_tag, # TODO: Calculate top tag per season
            representativePhoto=rep_photo_url,
            highlight=f"记录了{count}个精彩瞬间", # Mock highlight
            shootMonth=f"{months[0]}-{months[-1]}月" if len(months) > 1 else f"{months[0]}月"
        ))

    season_metrics = SeasonMetrics(seasonList=season_list)
    total_video_duration = db.query(func.sum(Photo.duration)).scalar() or 0
    # --- Emotion Metrics (Mock) ---
    # TODO: Implement Favorites/Sharing tracking
    emotion_metrics = EmotionMetrics(
        starredPhotos=128,
        backupPhotos=total_photos,
        totalVideoDuration=total_video_duration,
        totalOpenTimes=1024,
        starredPhotosList=[f"https://picsum.photos/seed/{i}/400/600" for i in range(6)],
        sharedPhotosList=[f"https://picsum.photos/seed/{i+10}/400/600" for i in range(3)],
        emotionCarouselGroups=[
            CarouselGroup(
                id='g1', 
                locationName='海边回忆', 
                photos=[f"https://picsum.photos/seed/{i+20}/400/600" for i in range(3)]
            )
        ]
    )

    # --- Easter Egg (Mock) ---
    easter_egg = EasterEgg(
        bestPhotoUrl=f"https://picsum.photos/seed/best/400/600",
        bestPhotoDate="2024-10-01",
        tags=EasterEggTags(main="生活记录家", sub=['偏爱人像', '乐于收藏', '心怀温柔'])
    )

    # --- User Info (Mock/Static) ---
    # TODO: Get real user info
    user_info = UserInfo(
        nickname="时光旅人",
        avatarUrl="/avatar.png"
    )

    return AnnualReportData(
        year=year,
        user=user_info,
        time=time_metrics,
        memory=memory_metrics,
        emotion=emotion_metrics,
        location=location_metrics,
        season=season_metrics,
        easterEgg=easter_egg
    )
