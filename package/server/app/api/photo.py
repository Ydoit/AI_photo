#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/12/7 23:20
@Author      : SiYuan
@Email       : sixyuan044@gmail.com
@File        : server-photo.py
@Description : 
"""
import logging
import time
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

import app.crud.photo
from app.core.config_manager import config_manager
from app.crud.photo import save_and_create_photo
from app.dependencies import get_db
from app.crud import album as crud_album
from app.crud import face as crud_face
from app.crud import tag as crud_tag

from app.schemas import photo as schemas
from app.schemas.metadata import PhotoMetadata, PhotoMetadataUpdate, PhotoDetail
from app.schemas import tag as tag_schemas
from app.service import storage
from app.service.task_manager import TaskManager
from app.db.models.task import TaskType
from app.api.deps import get_current_user
from app.db.models.user import User
import uuid
import os
import shutil

from app.db.models.image_description import ImageDescription as ImageDescriptionModel
from app.schemas.image_description import ImageDescription as ImageDescriptionSchema
from app.db.models.photo import Photo

router = APIRouter()

# Photo Endpoints

@router.get("/cleanup", response_model=List[schemas.Photo])
def get_photos_for_cleanup(
    skip: int = 0,
    limit: int = 50,
    sort_by: str = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Join with ImageDescription to access scores
    query = db.query(Photo).join(ImageDescriptionModel, Photo.id == ImageDescriptionModel.photo_id).filter(Photo.owner_id == current_user.id)

    # Calculate score: memory_score + quality_score
    # We use coalesce to treat nulls as 0
    score_expr = func.coalesce(ImageDescriptionModel.memory_score, 0) + func.coalesce(ImageDescriptionModel.quality_score, 0)

    if sort_by == "desc":
        query = query.order_by(score_expr.desc())
    else:
        query = query.order_by(score_expr.asc())

    photos = query.offset(skip).limit(limit).all()
    return photos


@router.get("", response_model=List[schemas.Photo])
def read_all_photos(
        skip: int = 0,
        limit: int = 100,
        album_id: Optional[UUID] = None,
        face_id: Optional[UUID] = None,
        tag_id: Optional[UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        years: Optional[List[int]] = Query(None),
        city: Optional[str] = None,
        cities: Optional[List[str]] = Query(None),
        province: Optional[str] = None,
        country: Optional[str] = None,
        make: Optional[str] = None,
        makes: Optional[List[str]] = Query(None),
        model: Optional[str] = None,
        models: Optional[List[str]] = Query(None),
        image_type: Optional[str] = None,
        image_types: Optional[List[str]] = Query(None),
        file_type: Optional[str] = None,
        file_types: Optional[List[str]] = Query(None),
        tag: Optional[str] = None,
        lat_min: Optional[float] = None,
        lat_max: Optional[float] = None,
        lng_min: Optional[float] = None,
        lng_max: Optional[float] = None,
        radius: Optional[float] = None,
        center_lat: Optional[float] = None,
        center_lng: Optional[float] = None,
        ids: Optional[List[UUID]] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    st_time = time.time()
    photos = app.crud.photo.get_all_photos(
        db, skip=skip, limit=limit, start_time=start_time, end_time=end_time,
        years=years, city=city, cities=cities, province=province, country=country, 
        make=make, makes=makes, model=model, models=models, 
        image_type=image_type, image_types=image_types, 
        file_type=file_type, file_types=file_types,
        tag=tag, album_id=album_id,
        face_id=face_id, tag_id=tag_id,
        lat_min=lat_min, lat_max=lat_max, lng_min=lng_min, lng_max=lng_max,
        radius=radius, center_lat=center_lat, center_lng=center_lng,
        ids=ids, user_id=current_user.id
    )
    logging.info(f"read_all_photos time: {time.time() - st_time}")
    return photos


@router.post("/batch/create")
def batch_create_photos(
    batch_data: schemas.BatchPhotoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Convert schema to dict list expected by crud
    photos_data = []
    for item in batch_data.items:
        photos_data.append({
            'photo': item.photo,
            'file_path': item.file_path,
            'photo_id': item.photo_id,
        })
    try:
        count = app.crud.photo.batch_create_photos(db, photos_data, user_id=current_user.id)
        return {"message": f"Successfully created {count} photos"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
def batch_update_photos(
        batch_data: schemas.BatchPhotoUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if batch_data.action in ['add_to_album', 'remove_from_album']:

        if not batch_data.album_id:
            raise HTTPException(status_code=400, detail="Album ID required for this action")

        if batch_data.action == 'add_to_album':
            # Verify album exists
            db_album = crud_album.get_album(db, album_id=batch_data.album_id, user_id=current_user.id)
            if not db_album:
                raise HTTPException(status_code=404, detail="Target album not found")

        count = crud_album.batch_update_album_association(db, batch_data.photo_ids, batch_data.album_id, batch_data.action, user_id=current_user.id)
        return {"message": f"Successfully updated {count} photos"}

    elif batch_data.action == 'delete':
        # Get photos to delete files
        photos = app.crud.photo.get_photos_by_ids(db, batch_data.photo_ids, user_id=current_user.id)
        for photo in photos:
            storage.delete_file(photo.owner_id, photo.file_path, photo.id)
            storage.delete_thumbnails(photo.owner_id, photo.id)
        app.crud.photo.batch_delete_photos_db(db, batch_data.photo_ids, user_id=current_user.id)
        return {"message": "Photos deleted successfully"}

    else:
        raise HTTPException(status_code=400, detail="Invalid action")


@router.delete("/batch")
def batch_delete_photos(
    batch_data: schemas.BatchPhotoDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    count = app.crud.photo.batch_delete_photos_db(db, batch_data.photo_ids, is_delete_file=True, user_id=current_user.id)
    return {"message": f"Successfully deleted {count} photos"}


@router.delete("/{photo_id}", response_model=schemas.Photo)
def delete_photo_global(photo_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_photo = app.crud.photo.delete_photo(db, photo_id=photo_id, is_delete_file=True, user_id=current_user.id)
    return db_photo


@router.put("/{photo_id}", response_model=schemas.Photo)
def update_photo(photo_id: UUID, photo: schemas.PhotoUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_photo = app.crud.photo.update_photo(db, photo_id, photo, user_id=current_user.id)
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return db_photo


# Metadata Endpoints

@router.get("/{photo_id}/metadata", response_model=PhotoMetadata)
def get_photo_metadata(photo_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_metadata = app.crud.photo.get_photo_metadata(db, photo_id=photo_id, user_id=current_user.id)

    if not db_metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")

    albums = crud_album.get_albums_by_photo_id(db, photo_id=photo_id)
    faces_identities = crud_face.get_identities_by_photo_id(db, photo_id=photo_id)
    tags = crud_tag.get_photo_tags(db, photo_id=photo_id)

    photo_metadata = PhotoMetadata.model_validate(db_metadata)
    photo_metadata.albums = albums
    photo_metadata.faces_identities = faces_identities
    photo_metadata.tags = tags

    return photo_metadata


@router.put("/{photo_id}/metadata", response_model=PhotoMetadata)
def update_photo_metadata(
        photo_id: UUID,
        metadata: PhotoMetadataUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = app.crud.photo.update_photo_metadata(db, photo_id=photo_id, metadata=metadata, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Photo not found or access denied")
    return result


# Tag Endpoints

@router.get("/{photo_id}/tags", response_model=List[tag_schemas.PhotoTagResponse])
def get_photo_tags(photo_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud_tag.get_photo_tags(db, photo_id, owner_id=current_user.id)


@router.post("/{photo_id}/tags", response_model=tag_schemas.PhotoTagResponse)
def add_photo_tag(photo_id: UUID, tag_data: tag_schemas.PhotoTagAdd, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check photo ownership? Usually yes.
    # But current implementation didn't check. Assuming user can tag photos they can see?
    # Or strict ownership? "Users only operate on their own."
    # So yes, check ownership.
    photo = app.crud.photo.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if photo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    return crud_tag.add_tag_to_photo(db, photo_id, tag_data.tag_name, tag_data.confidence, owner_id=current_user.id)


@router.delete("/{photo_id}/tags/{tag_id}")
def delete_photo_tag(photo_id: UUID, tag_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photo = app.crud.photo.get_photo(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if photo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    crud_tag.remove_tag_from_photo(db, photo_id, tag_id)
    return {"message": "Tag deleted successfully"}

@router.get("/{photo_id}/description", response_model=Optional[ImageDescriptionSchema], summary="获取图片描述")
def get_photo_description(
    photo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    desc = db.query(ImageDescriptionModel).filter(
        ImageDescriptionModel.photo_id == photo_id
    ).first()
    
    # Check ownership via photo
    if desc:
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo or photo.owner_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not authorized")
    
    return desc


@router.get("/on-this-day", response_model=List[PhotoDetail])
def get_on_this_day_photos(
    month: Optional[int] = None,
    day: Optional[int] = None,
    year: Optional[int] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取那年今日的照片
    """
    if month is None or day is None or year is None:
        now = datetime.now()
        month = month or now.month
        day = day or now.day
        year = year or now.year

    return app.crud.photo.get_on_this_day_photos(db, user_id=current_user.id, month=month, day=day, year=year, limit=limit)
