#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/12/7 23:20
@Author      : SiYuan
@Email       : siyuan044@gmail.com
@File        : server-photo.py
@Description : 
"""

from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from sqlalchemy.orm import Session
from itertools import groupby

from app.crud.album import save_and_create_photo
from app.dependencies import get_db
from app.crud import album as crud
from app.schemas import album as schemas
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
        year: Optional[str] = None,
        month: Optional[str] = None,
        day: Optional[str] = None,
        city: Optional[str] = None,
        tag: Optional[str] = None,
        db: Session = Depends(get_db)
):
    photos = crud.get_all_photos(db, skip=skip, limit=limit, year=year, month=month, day=day, city=city, tag=tag, album_id=album_id)
    return photos


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
            db_album = crud.get_album(db, album_id=batch_data.album_id)
            if not db_album:
                raise HTTPException(status_code=404, detail="Target album not found")

        count = crud.batch_update_album_association(db, batch_data.photo_ids, batch_data.album_id, batch_data.action)
        return {"message": f"Successfully updated {count} photos"}

    elif batch_data.action == 'delete':
        # Get photos to delete files
        photos = crud.get_photos_by_ids(db, batch_data.photo_ids)
        for photo in photos:
            storage.delete_file(photo.file_path, photo.id, db)

        crud.batch_delete_photos_db(db, batch_data.photo_ids)
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
        db_album = crud.get_album(db, album_id=album_id)
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
    db_photo = crud.delete_photo(db, photo_id=photo_id)
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Delete file from storage
    storage.delete_file(db_photo.file_path, db_photo.id, db)

    return db_photo


@router.put("/{photo_id}", response_model=schemas.Photo)
def update_photo(photo_id: UUID, photo: schemas.PhotoUpdate, db: Session = Depends(get_db)):
    db_photo = crud.update_photo(db, photo_id, photo)
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return db_photo


# Metadata Endpoints

@router.get("/{photo_id}/metadata", response_model=schemas.PhotoMetadata)
def read_photo_metadata(photo_id: UUID, db: Session = Depends(get_db)):
    # Ignoring album_id for metadata retrieval as it's global
    db_metadata = crud.get_photo_metadata(db, photo_id=photo_id)
    if not db_metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")
    return db_metadata


@router.put("/{photo_id}/metadata", response_model=schemas.PhotoMetadata)
def update_photo_metadata(
        photo_id: UUID,
        metadata: schemas.PhotoMetadataUpdate,
        db: Session = Depends(get_db)
):
    return crud.update_photo_metadata(db, photo_id=photo_id, metadata=metadata)


# Chunked Upload Endpoints

@router.post("/upload/init")
def init_upload():
    upload_id = uuid.uuid4()
    upload_dir = os.path.join("uploads", "chunks", str(upload_id))
    os.makedirs(upload_dir, exist_ok=True)
    return {"upload_id": upload_id}


@router.post("/upload/chunk")
def upload_chunk(
        upload_id: UUID = Form(...),
        chunk_index: int = Form(...),
        file: UploadFile = File(...)
):
    chunk_dir = os.path.join("uploads", "chunks", str(upload_id))
    if not os.path.exists(chunk_dir):
        raise HTTPException(status_code=404, detail="Upload session not found")

    chunk_path = os.path.join(chunk_dir, str(chunk_index))
    with open(chunk_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "success"}


@router.post("/upload/finish", response_model=schemas.Photo)
def finish_upload_generic(
        upload_id: UUID = Form(...),
        file_name: str = Form(...),
        album_id: Optional[UUID] = Form(None),
        db: Session = Depends(get_db)
):
    if album_id:
        # Verify album exists
        db_album = crud.get_album(db, album_id=album_id)
        if not db_album:
            raise HTTPException(status_code=404, detail="Album not found")

    # Merge chunks
    chunk_dir = os.path.join("uploads", "chunks", str(upload_id))
    if not os.path.exists(chunk_dir):
        raise HTTPException(status_code=404, detail="Upload session not found")

    chunks = sorted([int(f) for f in os.listdir(chunk_dir) if f.isdigit()])
    if not chunks:
        raise HTTPException(status_code=400, detail="No chunks found")

    photo_id = uuid.uuid4()
    ext = os.path.splitext(file_name)[1]

    # Save to storage_root/year/month with conflict resolution
    class _Tmp:
        filename = file_name
        file = None

    with open(os.path.join("uploads", "chunks", str(upload_id), "merged"), "wb") as outfile:
        for chunk_idx in chunks:
            chunk_path = os.path.join(chunk_dir, str(chunk_idx))
            with open(chunk_path, "rb") as infile:
                outfile.write(infile.read())
    with open(os.path.join("uploads", "chunks", str(upload_id), "merged"), "rb") as merged:
        _Tmp.file = merged
        final_path = storage.save_upload_file(_Tmp, photo_id, db)

    # Clean up chunks
    shutil.rmtree(chunk_dir)

    return save_and_create_photo(db, final_path, file_name, album_id, photo_id)
