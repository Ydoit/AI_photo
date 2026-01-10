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

class ReportSummary(BaseModel):
    user: UserInfo
    time: TimeMetrics

def get_date_range_filter(query, start_time: datetime, end_time: datetime):
    return query.filter(
        Photo.photo_time >= start_time,
        Photo.photo_time <= end_time
    )

def get_annual_report_photos(
    start_time: datetime,
    end_time: datetime,
    db: Session
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

        monthly_groups[month].append(p)

    # 每个月随机选10张照片
    for month in monthly_groups:
        random.shuffle(monthly_groups[month])
        monthly_groups[month] = monthly_groups[month][:10]

    return monthly_groups

def get_report_expenses(
    start_time: datetime,
    end_time: datetime,
    db: Session
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

def get_report_summary(
    start_time: datetime,
    end_time: datetime,
    db: Session
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


def get_report_season(
    start_time: datetime,
    end_time: datetime,
    db: Session
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

def get_report_emotion(
    start_time: datetime,
    end_time: datetime,
    db: Session
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