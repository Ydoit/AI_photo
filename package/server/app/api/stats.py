from uuid import UUID
import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract

from app.dependencies import get_db
from app.db.models.photo import Photo
from app.db.models.album import Album
from app.schemas.album import TimelineItem, TimelineStats
from app.schemas.dashboard import DashboardResponse
from app.crud import dashboard as crud_dashboard

router = APIRouter()

@router.get('/timeline', response_model=TimelineStats)
def get_timeline_stats(album_id: UUID|None = None, db: Session = Depends(get_db)):
    if album_id is None:
        # 不指定相册时，返回所有照片的统计
        query = db.query(Photo)
    else:
        # 指定相册时，只返回该相册的照片
        query = db.query(Photo).join(Photo.albums).filter(Album.id == album_id).options(joinedload(Photo.albums))
    # 总数
    total = query.count()

    if total == 0:
        return TimelineStats(total_photos=0, time_range=None, timeline=[])

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
            if min_time is None or y < min_time.year or (y == min_time.year and m < min_time.month) or (y == min_time.year and m == min_time.month and d < min_time.day):
                min_time = datetime.datetime(int(y), int(m), int(d))
            if max_time is None or y > max_time.year or (y == max_time.year and m > max_time.month) or (y == max_time.year and m == max_time.month and d > max_time.day):
                max_time = datetime.datetime(int(y), int(m), int(d))

    return {
        'total_photos': total,
        'time_range': {
            'start': min_time.isoformat() if min_time else None,
            'end': max_time.isoformat() if max_time else None
        },
        'timeline': timeline
    }

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard_overview(db: Session = Depends(get_db)):
    """
    Get dashboard overview data.
    """
    return crud_dashboard.get_dashboard_stats(db)