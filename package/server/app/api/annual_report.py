from typing import List, Optional, Dict
from datetime import datetime
import random
import math
import logging

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc
from pydantic import BaseModel

from app.dependencies import get_db
from app.db.models.photo import Photo, ImageType, FileType
from app.db.models.photo_metadata import PhotoMetadata
from app.db.models.face import Face, FaceIdentity
from app.db.models.tag import PhotoTag, PhotoTagRelation
from app.db.models.trip import TrainTicket
from app.schemas.annual_report import (
    AnnualReportData, UserInfo, TimeMetrics, MemoryMetrics, 
    EmotionMetrics, LocationMetrics, SeasonMetrics, SeasonData,
    EasterEgg, EasterEggTags, CategoryDistributionItem, TopCity,
    LocationPoint, CarouselGroup, ExpenseMetrics, MonthlyExpense,
    TicketDetail, TravelBehaviorMetrics, ComprehensiveMetrics,
    MonthlyFrequency, RouteStats, DestinationStats, TripTypeDistribution,
    TransportAnalysisMetrics
)

router = APIRouter()
logger = logging.getLogger(__name__)

from app.schemas.photo import Photo as PhotoSchema

@router.get("/transport-analysis", response_model=TransportAnalysisMetrics)
def get_report_transport_analysis(
    start_time: datetime = Query(..., description="Start Time"),
    end_time: datetime = Query(..., description="End Time"),
    db: Session = Depends(get_db)
):
    behavior = get_report_travel_behavior(start_time, end_time, db)
    comprehensive = get_report_comprehensive(start_time, end_time, db)
    return TransportAnalysisMetrics(
        behavior=behavior,
        comprehensive=comprehensive
    )
@router.get("/photos", response_model=Dict[int, List[PhotoSchema]])
def get_annual_report_photos(
    start_time: datetime = Query(..., description="Start Time"),
    end_time: datetime = Query(..., description="End Time"),
    db: Session = Depends(get_db)
):
    # Query photos within the time range, ordered by time descending
    photos = db.query(Photo).join(PhotoMetadata, PhotoMetadata.photo_id == Photo.id)\
    .filter(
        Photo.photo_time >= start_time,
        Photo.photo_time <= end_time
    )\
    .filter(Photo.file_type == FileType.image)\
    .filter(Photo.image_type != ImageType.SCREENSHOT)\
    .filter(PhotoMetadata.exif_info.isnot(None))\
    .order_by(Photo.photo_time.desc()).all()

    # Group by month
    monthly_groups: Dict[int, List[PhotoSchema]] = {}

    # We can iterate and filter.
    # Since we need max 10 per month, and we sorted by time desc,
    # we can just fill the buckets until they are full.

    for p in photos:
        if not p.photo_time:
            continue
        month = p.photo_time.month
        if month not in monthly_groups:
            monthly_groups[month] = []

        if len(monthly_groups[month]) < 10:
            monthly_groups[month].append(p)

    return monthly_groups


@router.get("/expenses", response_model=ExpenseMetrics)
def get_report_expenses(
    start_time: datetime = Query(..., description="Start Time"),
    end_time: datetime = Query(..., description="End Time"),
    db: Session = Depends(get_db)
):
    query = db.query(TrainTicket).filter(
        TrainTicket.date_time >= start_time,
        TrainTicket.date_time <= end_time
    )
    
    total_count = query.count()
    
    # Calculate total amount
    total_amount_result = query.with_entities(func.sum(TrainTicket.price)).scalar()
    total_amount = float(total_amount_result) if total_amount_result else 0.0
    
    average_price = total_amount / total_count if total_count > 0 else 0.0
    
    # Max expense
    max_expense_ticket = query.order_by(TrainTicket.price.desc()).first()
    max_expense_amount = float(max_expense_ticket.price) if max_expense_ticket else 0.0
    max_expense_name = f"{max_expense_ticket.train_code} ({max_expense_ticket.departure_station}-{max_expense_ticket.arrival_station})" if max_expense_ticket else None
    
    # Monthly trend
    # Group by month
    monthly_data = db.query(
        extract('year', TrainTicket.date_time).label('year'),
        extract('month', TrainTicket.date_time).label('month'),
        func.sum(TrainTicket.price).label('amount')
    ).filter(
        TrainTicket.date_time >= start_time,
        TrainTicket.date_time <= end_time
    ).group_by(
        'year', 'month'
    ).order_by(
        'year', 'month'
    ).all()
    
    monthly_trend = []
    for row in monthly_data:
        # row is (year, month, amount)
        monthly_trend.append(MonthlyExpense(
            month=f"{int(row.year)}-{int(row.month):02d}",
            amount=float(row.amount)
        ))

    # Last Year Comparison
    try:
        start_time_last_year = start_time.replace(year=start_time.year - 1)
        end_time_last_year = end_time.replace(year=end_time.year - 1)
    except ValueError:
        # Handle leap year case if necessary (e.g. Feb 29)
        start_time_last_year = start_time.replace(year=start_time.year - 1, day=28)
        end_time_last_year = end_time.replace(year=end_time.year - 1, day=28)

    query_last_year = db.query(TrainTicket).filter(
        TrainTicket.date_time >= start_time_last_year,
        TrainTicket.date_time <= end_time_last_year
    )
    total_amount_last_year_result = query_last_year.with_entities(func.sum(TrainTicket.price)).scalar()
    total_amount_last_year = float(total_amount_last_year_result) if total_amount_last_year_result else 0.0

    monthly_data_last_year = db.query(
        extract('year', TrainTicket.date_time).label('year'),
        extract('month', TrainTicket.date_time).label('month'),
        func.sum(TrainTicket.price).label('amount')
    ).filter(
        TrainTicket.date_time >= start_time_last_year,
        TrainTicket.date_time <= end_time_last_year
    ).group_by(
        'year', 'month'
    ).order_by(
        'year', 'month'
    ).all()

    monthly_trend_last_year = []
    for row in monthly_data_last_year:
        monthly_trend_last_year.append(MonthlyExpense(
            month=f"{int(row.year)}-{int(row.month):02d}",
            amount=float(row.amount)
        ))
        
    return ExpenseMetrics(
        totalAmount=total_amount,
        totalCount=total_count,
        averagePrice=average_price,
        monthlyTrend=monthly_trend,
        totalAmountLastYear=total_amount_last_year,
        monthlyTrendLastYear=monthly_trend_last_year,
        maxExpenseTicket=max_expense_name,
        maxExpenseAmount=max_expense_amount
    )

@router.get("/expenses/details", response_model=List[TicketDetail])
def get_report_expense_details(
    start_time: datetime = Query(..., description="Start Time"),
    end_time: datetime = Query(..., description="End Time"),
    db: Session = Depends(get_db)
):
    try:
        tickets = db.query(TrainTicket).filter(
            TrainTicket.date_time >= start_time,
            TrainTicket.date_time <= end_time
        ).order_by(TrainTicket.date_time.desc()).all()
        
        result = []
        for t in tickets:
            result.append(TicketDetail(
                id=str(t.id),
                train_code=t.train_code,
                departure_station=t.departure_station,
                arrival_station=t.arrival_station,
                date_time=t.date_time,
                price=float(t.price),
                seat_type=t.seat_type,
                name=t.name
            ))
        return result
    except Exception as e:
        logger.error(f"Failed to fetch expense details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch expense details")


def get_date_range_filter(query, start_time: datetime, end_time: datetime):
    return query.filter(
        Photo.photo_time >= start_time,
        Photo.photo_time <= end_time
    )

class ReportSummary(BaseModel):
    user: UserInfo
    time: TimeMetrics

@router.get("/summary", response_model=ReportSummary)
def get_report_summary(
    start_time: datetime = Query(..., description="Start Time"),
    end_time: datetime = Query(..., description="End Time"),
    db: Session = Depends(get_db)
):
    base_query = get_date_range_filter(db.query(Photo), start_time, end_time)
    total_photos = base_query.count()

    # --- Time Metrics ---
    accompany_days = base_query.with_entities(func.date(Photo.photo_time)).distinct().count()

    first_photo = base_query.order_by(Photo.photo_time.asc()).first()
    last_photo = base_query.order_by(Photo.photo_time.desc()).first()

    late_night_count = base_query.filter(extract('hour', Photo.photo_time) < 5).count()

    # Get all dates with photos
    photo_dates_rows = base_query.with_entities(func.date(Photo.photo_time)).distinct().all()
    photo_dates = [str(row[0]) for row in photo_dates_rows]

    time_metrics = TimeMetrics(
        totalPhotos=total_photos,
        accompanyDays=accompany_days,
        firstPhotoDate=first_photo.photo_time.strftime('%Y-%m-%d') if first_photo else None,
        lastPhotoDate=last_photo.photo_time.strftime('%Y-%m-%d') if last_photo else None,
        lateNightPhotoCount=late_night_count,
        photoDates=photo_dates
    )

    # --- User Info (Mock/Static) ---
    user_info = UserInfo(
        nickname="时光旅人",
        avatarUrl="/avatar.png"
    )

    return ReportSummary(user=user_info, time=time_metrics)


@router.get("/memory", response_model=MemoryMetrics)
def get_report_memory(
    start_time: datetime = Query(..., description="Start Time"),
    end_time: datetime = Query(..., description="End Time"),
    db: Session = Depends(get_db)
):
    base_query = get_date_range_filter(db.query(Photo), start_time, end_time)
    total_photos = base_query.count()

    # --- Memory Metrics ---
    # Category Distribution (Top Tags)
    top_tags = db.query(PhotoTag.tag_name, func.count(PhotoTagRelation.photo_id).label('count'))\
        .join(PhotoTagRelation, PhotoTag.id == PhotoTagRelation.tag_id)\
        .join(Photo, Photo.id == PhotoTagRelation.photo_id)\
        .join(PhotoMetadata, PhotoMetadata.photo_id == Photo.id)\
        .filter(Photo.file_type == FileType.image)\
        .filter(Photo.image_type != ImageType.SCREENSHOT)\
        .filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time)\
        .filter(PhotoMetadata.exif_info.isnot(None))\
        .group_by(PhotoTag.tag_name)\
        .order_by(desc('count'))\
        .limit(50).all()

    exclude_tags = {"二维码", "文档/截图"}
    category_distribution = [CategoryDistributionItem(name=t[0], value=t[1]) for t in top_tags if t[0] not in exclude_tags][:5]
    if not category_distribution:
        category_distribution = [CategoryDistributionItem(name="生活日常", value=total_photos)]

    # Top Person
    top_person = db.query(FaceIdentity.identity_name, func.count(Face.id).label('count'))\
        .join(Face, Face.face_identity_id == FaceIdentity.id)\
        .join(Photo, Photo.id == Face.photo_id)\
        .filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time)\
        .group_by(FaceIdentity.identity_name)\
        .order_by(desc('count')).first()

    top_person_name = top_person[0] if top_person else ""
    top_person_count = top_person[1] if top_person else 0

    # Top Location
    top_location_row = db.query(PhotoMetadata.city, func.count(Photo.id).label('count'))\
        .join(Photo, Photo.id == PhotoMetadata.photo_id)\
        .filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time)\
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

    max_photo_day = str(max_photo_day_row[0]) if max_photo_day_row else start_time.strftime('%Y-%m-%d')
    max_photo_day_count = max_photo_day_row[1] if max_photo_day_row else 0

    # Top Feature (Camera Make and Model)
    top_feature_row = db.query(PhotoMetadata.make, PhotoMetadata.model, func.count(Photo.id).label('count'))\
        .join(Photo, Photo.id == PhotoMetadata.photo_id)\
        .filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time)\
        .filter(PhotoMetadata.make.isnot(None), PhotoMetadata.model.isnot(None))\
        .group_by(PhotoMetadata.make, PhotoMetadata.model)\
        .order_by(desc('count')).first()

    top_feature = f"{top_feature_row[0]} {top_feature_row[1]}" if top_feature_row else "未知"
    top_feature_count = top_feature_row[2] if top_feature_row else 0

    return MemoryMetrics(
        categoryDistribution=category_distribution,
        topPersonName=top_person_name,
        topPersonCount=top_person_count,
        topLocation=top_location,
        maxPhotoDay=max_photo_day,
        maxPhotoDayCount=max_photo_day_count,
        topFeature=top_feature,
        topFeatureCount=top_feature_count,
        topMake=top_feature_row[0] if top_feature_row else "",
        topModel=top_feature_row[1] if top_feature_row else "",
        topMakeModelCount=top_feature_count
    )


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r

@router.get("/location", response_model=LocationMetrics)
def get_report_location(
    start_time: datetime = Query(..., description="Start Time"),
    end_time: datetime = Query(..., description="End Time"),
    db: Session = Depends(get_db)
):
    # --- Location Metrics ---
    lighten_province = db.query(func.count(func.distinct(PhotoMetadata.province)))\
        .join(Photo, Photo.id == PhotoMetadata.photo_id)\
        .filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time).scalar()

    lighten_city = db.query(func.count(func.distinct(PhotoMetadata.city)))\
        .join(Photo, Photo.id == PhotoMetadata.photo_id)\
        .filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time).scalar()

    # Top Cities
    top_cities_rows = db.query(PhotoMetadata.city, PhotoMetadata.province, func.count(Photo.id).label('count'))\
        .join(Photo, Photo.id == PhotoMetadata.photo_id)\
        .filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time)\
        .filter(PhotoMetadata.city.isnot(None))\
        .group_by(PhotoMetadata.city, PhotoMetadata.province)\
        .order_by(desc('count'))\
        .limit(3).all()

    top_cities = [TopCity(cityName=row[0], provinceName=row[1] or "", photoCount=row[2]) for row in top_cities_rows]

    # Location Points
    points_rows = db.query(
        func.avg(PhotoMetadata.longitude),
        func.avg(PhotoMetadata.latitude),
        PhotoMetadata.city,
        func.count(Photo.id)
    )\
    .join(Photo, Photo.id == PhotoMetadata.photo_id)\
    .filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time)\
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
            
        cover_photo = db.query(Photo).join(PhotoMetadata)\
            .filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time)\
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

    # Calculate Farthest City
    farthest_city = None
    farthest_distance = 0.0
    farthest_city_photos = []

    # 1. Find the "Current City" (Top 1 by photo count)
    top_city_ref = db.query(
        PhotoMetadata.city,
        func.avg(PhotoMetadata.latitude),
        func.avg(PhotoMetadata.longitude)
    )\
    .join(Photo, Photo.id == PhotoMetadata.photo_id)\
    .filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time)\
    .filter(PhotoMetadata.city.isnot(None))\
    .group_by(PhotoMetadata.city)\
    .order_by(desc(func.count(Photo.id)))\
    .first()

    if top_city_ref and top_city_ref[1] and top_city_ref[2]:
        curr_city_name = top_city_ref[0]
        curr_lat = float(top_city_ref[1])
        curr_lng = float(top_city_ref[2])

        # 2. Get all other cities with coordinates
        other_cities = db.query(
            PhotoMetadata.city,
            func.avg(PhotoMetadata.latitude),
            func.avg(PhotoMetadata.longitude)
        )\
        .join(Photo, Photo.id == PhotoMetadata.photo_id)\
        .filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time)\
        .filter(PhotoMetadata.city.isnot(None))\
        .filter(PhotoMetadata.city != curr_city_name)\
        .filter(PhotoMetadata.latitude.isnot(None))\
        .filter(PhotoMetadata.longitude.isnot(None))\
        .group_by(PhotoMetadata.city)\
        .all()

        max_dist = 0.0
        target_city_name = None

        for row in other_cities:
            city_name, lat, lng = row
            dist = haversine_distance(curr_lat, curr_lng, float(lat), float(lng))
            if dist > max_dist:
                max_dist = dist
                target_city_name = city_name

        if target_city_name:
            farthest_city = target_city_name
            farthest_distance = round(max_dist, 2)

            # Get 10 photos from farthest city
            f_photos = db.query(Photo).join(PhotoMetadata)\
                .filter(Photo.photo_time >= start_time, Photo.photo_time <= end_time)\
                .filter(PhotoMetadata.city == target_city_name)\
                .limit(20).all()

            farthest_city_photos = f_photos

    return LocationMetrics(
        lightenProvinceNum=lighten_province or 0,
        lightenCityNum=lighten_city or 0,
        topCities=top_cities,
        locationPoints=location_points,
        farthestCity=farthest_city,
        farthestDistance=int(farthest_distance),
        farthestCityPhotos=farthest_city_photos
    )


@router.get("/season", response_model=SeasonMetrics)
def get_report_season(
    start_time: datetime = Query(..., description="Start Time"),
    end_time: datetime = Query(..., description="End Time"),
    db: Session = Depends(get_db)
):
    base_query = get_date_range_filter(db.query(Photo), start_time, end_time)
    
    seasons_def = [
        ("春", [3, 4, 5], "嫩芽"),
        ("夏", [6, 7, 8], "蝉鸣"),
        ("秋", [9, 10, 11], "晚风"),
        ("冬", [12, 1, 2], "暖意")
    ]
    season_list = []
    
    for name, months, default_tag in seasons_def:
        season_query = base_query.filter(Photo.file_type == FileType.image)\
            .filter(Photo.image_type != ImageType.SCREENSHOT)\
            .filter(extract('month', Photo.photo_time).in_(months))
        count = season_query.count()

        rep_photo = season_query.first()
        rep_photo_url = f"/api/medias/{rep_photo.id}/thumbnail" if rep_photo else f"https://picsum.photos/seed/{name}/400/600"
        # rep_photo_url = f"https://picsum.photos/seed/{name}/400/600"
        season_list.append(SeasonData(
            seasonName=name,
            photoCount=count,
            topTag=default_tag, 
            representativePhoto=rep_photo_url,
            highlight=f"记录了{count}个精彩瞬间", 
            shootMonth=f"{months[0]}-{months[-1]}月" if len(months) > 1 else f"{months[0]}月"
        ))

    return SeasonMetrics(seasonList=season_list)


@router.get("/emotion", response_model=EmotionMetrics)
def get_report_emotion(
    start_time: datetime = Query(..., description="Start Time"),
    end_time: datetime = Query(..., description="End Time"),
    db: Session = Depends(get_db)
):
    base_query = get_date_range_filter(db.query(Photo), start_time, end_time)
    total_photos = base_query.count()
    total_video_duration = db.query(func.sum(Photo.duration)).filter(
        Photo.photo_time >= start_time,
        Photo.photo_time <= end_time
    ).scalar() or 0

    return EmotionMetrics(
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


@router.get("/easter-egg", response_model=EasterEgg)
def get_report_easter_egg(
    start_time: datetime = Query(..., description="Start Time"),
    end_time: datetime = Query(..., description="End Time"),
    db: Session = Depends(get_db)
):
    return EasterEgg(
        bestPhotoUrl=f"https://picsum.photos/seed/best/400/600",
        bestPhotoDate="2024-10-01",
        tags=EasterEggTags(main="生活记录家", sub=['偏爱人像', '乐于收藏', '心怀温柔'])
    )

@router.get("/travel-behavior", response_model=TravelBehaviorMetrics)
def get_report_travel_behavior(
    start_time: datetime = Query(..., description="Start Time"),
    end_time: datetime = Query(..., description="End Time"),
    db: Session = Depends(get_db)
):
    # Monthly Frequency
    monthly_data = db.query(
        extract('year', TrainTicket.date_time).label('year'),
        extract('month', TrainTicket.date_time).label('month'),
        func.count(TrainTicket.id).label('count')
    ).filter(
        TrainTicket.date_time >= start_time,
        TrainTicket.date_time <= end_time
    ).group_by(
        'year', 'month'
    ).order_by(
        'year', 'month'
    ).all()

    monthly_frequency = [
        MonthlyFrequency(month=f"{int(row.year)}-{int(row.month):02d}", count=int(row.count))
        for row in monthly_data
    ]

    # Top Routes
    top_routes_data = db.query(
        TrainTicket.departure_station,
        TrainTicket.arrival_station,
        func.count(TrainTicket.id).label('count')
    ).filter(
        TrainTicket.date_time >= start_time,
        TrainTicket.date_time <= end_time
    ).group_by(
        TrainTicket.departure_station,
        TrainTicket.arrival_station
    ).order_by(
        desc('count')
    ).limit(5).all()

    top_routes = [
        RouteStats(route=f"{row.departure_station} -> {row.arrival_station}", count=int(row.count))
        for row in top_routes_data
    ]

    # Top Destinations
    top_destinations_data = db.query(
        TrainTicket.arrival_station,
        func.count(TrainTicket.id).label('count')
    ).filter(
        TrainTicket.date_time >= start_time,
        TrainTicket.date_time <= end_time
    ).group_by(
        TrainTicket.arrival_station
    ).order_by(
        desc('count')
    ).limit(5).all()

    top_destinations = [
        DestinationStats(city=row.arrival_station, count=int(row.count))
        for row in top_destinations_data
    ]

    # Trip Type Distribution
    tickets = db.query(TrainTicket).filter(
        TrainTicket.date_time >= start_time,
        TrainTicket.date_time <= end_time
    ).all()
    
    workday_count = 0
    weekend_count = 0
    holiday_count = 0 
    
    for t in tickets:
        wd = t.date_time.weekday() # 0-6, 5=Sat, 6=Sun
        if wd >= 5:
            weekend_count += 1
        else:
            workday_count += 1
            
    return TravelBehaviorMetrics(
        monthlyFrequency=monthly_frequency,
        topRoutes=top_routes,
        topDestinations=top_destinations,
        tripTypeDistribution=TripTypeDistribution(
            workday=workday_count,
            weekend=weekend_count,
            holiday=holiday_count
        )
    )

@router.get("/comprehensive", response_model=ComprehensiveMetrics)
def get_report_comprehensive(
    start_time: datetime = Query(..., description="Start Time"),
    end_time: datetime = Query(..., description="End Time"),
    db: Session = Depends(get_db)
):
    query = db.query(TrainTicket).filter(
        TrainTicket.date_time >= start_time,
        TrainTicket.date_time <= end_time
    )
    
    # Total Mileage
    total_mileage_result = query.with_entities(func.sum(TrainTicket.total_mileage)).scalar()
    total_mileage = int(total_mileage_result) if total_mileage_result else 0
    
    # Cost per Km
    total_price_result = query.with_entities(func.sum(TrainTicket.price)).scalar()
    total_price = float(total_price_result) if total_price_result else 0.0
    
    cost_per_km = total_price / total_mileage if total_mileage > 0 else 0.0
    
    return ComprehensiveMetrics(
        totalMileage=total_mileage,
        costPerKm=round(cost_per_km, 2)
    )