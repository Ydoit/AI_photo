#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/12/7 23:20
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-photo.py
@Description : 
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.config_manager import config_manager
from app.crud.album import save_and_create_photo
from app.dependencies import get_db
from app.crud import album as crud_album
from app.crud import face as crud_face

from app.schemas import photo as schemas
from app.schemas.metadata import PhotoMetadata, PhotoMetadataUpdate
from app.service import storage
import uuid
import os
import shutil

router = APIRouter()

# Photo Endpoints

@router.get("", response_model=List[schemas.Photo])
def read_all_photos(
        skip: int = 0,
        limit: int = 100,
        album_id: Optional[UUID] = None,
        face_id: Optional[UUID] = None,
        tag_id: Optional[UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        country: Optional[str] = None,
        tag: Optional[str] = None,
        lat_min: Optional[float] = None,
        lat_max: Optional[float] = None,
        lng_min: Optional[float] = None,
        lng_max: Optional[float] = None,
        radius: Optional[float] = None,
        center_lat: Optional[float] = None,
        center_lng: Optional[float] = None,
        db: Session = Depends(get_db)
):
    photos = crud_album.get_all_photos(
        db, skip=skip, limit=limit, start_time=start_time, end_time=end_time,
        city=city, province=province, country=country, tag=tag, album_id=album_id,
        face_id=face_id, tag_id=tag_id,
        lat_min=lat_min, lat_max=lat_max, lng_min=lng_min, lng_max=lng_max,
        radius=radius, center_lat=center_lat, center_lng=center_lng
    )
    return photos


@router.post("/batch/create")
def batch_create_photos(
    batch_data: schemas.BatchPhotoCreate,
    db: Session = Depends(get_db)
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
        count = crud_album.batch_create_photos(db, photos_data)
        return {"message": f"Successfully created {count} photos"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
def batch_update_photos(
        batch_data: schemas.BatchPhotoUpdate,
        db: Session = Depends(get_db)
):
    if batch_data.action in ['add_to_album', 'remove_from_album']:

        if not batch_data.album_id:
            raise HTTPException(status_code=400, detail="Album ID required for this action")

        if batch_data.action == 'add_to_album':
            # Verify album exists
            db_album = crud_album.get_album(db, album_id=batch_data.album_id)
            if not db_album:
                raise HTTPException(status_code=404, detail="Target album not found")

        count = crud_album.batch_update_album_association(db, batch_data.photo_ids, batch_data.album_id, batch_data.action)
        return {"message": f"Successfully updated {count} photos"}

    elif batch_data.action == 'delete':
        # Get photos to delete files
        photos = crud_album.get_photos_by_ids(db, batch_data.photo_ids)
        for photo in photos:
            storage.delete_file(photo.file_path, photo.id, db)

        crud_album.batch_delete_photos_db(db, batch_data.photo_ids)
        return {"message": "Photos deleted successfully"}

    else:
        raise HTTPException(status_code=400, detail="Invalid action")


@router.post("", response_model=schemas.Photo)
async def upload_photo_generic(
        album_id: Optional[UUID] = Form(None),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    if album_id:
        # Verify album exists
        db_album = crud_album.get_album(db, album_id=album_id)
        if not db_album:
            raise HTTPException(status_code=404, detail="Album not found")

    # Generate ID
    photo_id = uuid.uuid4()

    # Save file
    file_path = storage.save_upload_file(file, photo_id, db)

    # Create and Save
    return save_and_create_photo(db, file_path, file.filename, album_id, photo_id)

@router.delete("/{photo_id}", response_model=schemas.Photo)
def delete_photo_global(photo_id: UUID, db: Session = Depends(get_db)):
    db_photo = crud_album.delete_photo(db, photo_id=photo_id)
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Delete file from storage
    storage.delete_file(db_photo.file_path, db_photo.id, db)

    return db_photo


@router.put("/{photo_id}", response_model=schemas.Photo)
def update_photo(photo_id: UUID, photo: schemas.PhotoUpdate, db: Session = Depends(get_db)):
    db_photo = crud_album.update_photo(db, photo_id, photo)
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return db_photo


# Metadata Endpoints

@router.get("/{photo_id}/metadata", response_model=PhotoMetadata)
def read_photo_metadata(photo_id: UUID, db: Session = Depends(get_db)):
    # Ignoring album_id for metadata retrieval as it's global
    db_metadata = crud_album.get_photo_metadata(db, photo_id=photo_id)
    albums = crud_album.get_albums_by_photo_id(db, photo_id=photo_id)
    faces_identities = crud_face.get_identities_with_details(db, photo_id=photo_id)

    if not db_metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")
    photo_metadata = PhotoMetadata.model_validate(db_metadata)
    photo_metadata.albums = albums
    photo_metadata.faces_identities = faces_identities
    return photo_metadata


@router.put("/{photo_id}/metadata", response_model=PhotoMetadata)
def update_photo_metadata(
        photo_id: UUID,
        metadata: PhotoMetadataUpdate,
        db: Session = Depends(get_db)
):
    return crud_album.update_photo_metadata(db, photo_id=photo_id, metadata=metadata)

