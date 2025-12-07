from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.dependencies import get_db
from app.db.models.photo import Photo

router = APIRouter()

@router.get('/stats/timeline')
def get_timeline_stats(db: Session = Depends(get_db)):
    # Total count
    total = db.query(Photo).count()
    
    # Time range
    min_time = db.query(func.min(Photo.photo_time)).scalar()
    max_time = db.query(func.max(Photo.photo_time)).scalar()
    
    # Group by Year-Month
    # SQLite/PostgreSQL differences in date truncation.
    # Assuming standard SQLAlchemy usage, we might need to be careful with DB specifics.
    # But since user mentioned PostgreSQL in project_rules, we can use extract or date_trunc.
    # However, if using SQLite for dev, extract is safer.
    
    # Using extract for broader compatibility (year, month)
    timeline_query = db.query(
        func.extract('year', Photo.photo_time).label('year'),
        func.extract('month', Photo.photo_time).label('month'),
        func.count(Photo.id).label('count')
    ).group_by(
        func.extract('year', Photo.photo_time),
        func.extract('month', Photo.photo_time)
    ).order_by(
        func.extract('year', Photo.photo_time).desc(),
        func.extract('month', Photo.photo_time).desc()
    ).all()
    
    timeline = []
    for y, m, c in timeline_query:
        if y is not None and m is not None:
            timeline.append({
                'year': int(y),
                'month': int(m),
                'count': c
            })
            
    return {
        'total_photos': total,
        'time_range': {
            'start': min_time,
            'end': max_time
        },
        'timeline': timeline
    }
