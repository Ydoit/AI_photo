from uuid import UUID
from typing import List, Optional
import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract

from app.db.models import User
from app.dependencies import get_db
from app.db.models.photo import Photo
from app.db.models.album import Album
from app.schemas.album import TimelineItem, TimelineStats
from app.schemas.dashboard import DashboardResponse
from app.schemas.filter import FilterOptions
from app.crud import dashboard as crud_dashboard
from app.crud import album as crud_album
from app.api.deps import get_current_user

router = APIRouter()

@router.get('/timeline', response_model=TimelineStats)
def get_timeline_stats(
    album_id: UUID|None = None,
    years: Optional[List[int]] = Query(None),
    cities: Optional[List[str]] = Query(None),
    makes: Optional[List[str]] = Query(None),
    models: Optional[List[str]] = Query(None),
    image_types: Optional[List[str]] = Query(None),
    file_types: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud_album.get_timeline_stats(
        db,
        album_id=album_id,
        years=years,
        cities=cities,
        makes=makes,
        models=models,
        image_types=image_types,
        file_types=file_types,
        user_id=current_user.id
    )

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get dashboard overview data.
    """
    return crud_dashboard.get_dashboard_stats(db, owner_id=current_user.id)

@router.get("/filters", response_model=FilterOptions)
def get_filter_options(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get all available filter options.
    """
    return crud_album.get_filter_options(db, user_id=current_user.id)
