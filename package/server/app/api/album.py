from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from sqlalchemy.orm import Session

from app.api.photo import upload_photo_generic
from app.dependencies import get_db
from app.crud import album as crud
from app.schemas import album as schemas


router = APIRouter()

# Album Endpoints

@router.post("", response_model=schemas.Album)
def create_album(album: schemas.AlbumCreate, db: Session = Depends(get_db)):
    return crud.create_album(db=db, album=album)

@router.get("", response_model=List[schemas.Album])
def read_albums(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_albums(db, skip=skip, limit=limit)

@router.get("/{album_id}", response_model=schemas.Album)
def read_album(album_id: UUID, db: Session = Depends(get_db)):
    db_album = crud.get_album(db, album_id=album_id)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    
    # Check if cover is set (relationship or ID)
    if db_album.cover_id is None:
        photos = crud.get_photos(db, album_id)
        if photos:
            earliest = min(photos, key=lambda p: p.photo_time or p.upload_time)
            try:
                # Assign ID and refresh or assign object
                db_album.cover_id = earliest.id
                db_album.cover = earliest
                db.add(db_album)
                db.commit()
            except Exception:
                pass
    return db_album

@router.delete("/{album_id}", response_model=schemas.Album)
def delete_album(album_id: UUID, db: Session = Depends(get_db)):
    db_album = crud.delete_album(db, album_id=album_id)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    return db_album

@router.put("/{album_id}", response_model=schemas.Album)
def update_album(album_id: UUID, album: schemas.AlbumCreate, db: Session = Depends(get_db)):
    db_album = crud.update_album(db, album_id=album_id, album=album)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    return db_album

@router.put("/{album_id}/cover", response_model=schemas.Album)
def set_album_cover(album_id: UUID, payload: dict, db: Session = Depends(get_db)):
    photo_id = payload.get('photo_id')
    if not photo_id:
        raise HTTPException(status_code=400, detail="photo_id required")
    db_album = crud.get_album(db, album_id=album_id)
    if not db_album:
        raise HTTPException(status_code=404, detail="Album not found")
    photo = crud.get_photo(db, UUID(str(photo_id)))
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    db_album.cover_id = photo.id
    db_album.cover = photo
    db.commit()
    db.refresh(db_album)
    return db_album


@router.post("/{album_id}/photos", response_model=schemas.Photo)
async def upload_photo(
        album_id: UUID,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    # Forward to generic handler
    return await upload_photo_generic(album_id, file, db)


@router.get("/{album_id}/photos", response_model=List[schemas.Photo])
def read_photos(album_id: UUID, skip: int = 0, limit: int = 100, year: Optional[str] = None, month: Optional[str] = None, day: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_photos(db, album_id=album_id, skip=skip, limit=limit, year=year, month=month, day=day)


@router.delete("/{album_id}/photos/{photo_id}", response_model=schemas.Photo)
def delete_photo(album_id: UUID, photo_id: UUID, db: Session = Depends(get_db)):
    # Remove association
    count = crud.batch_update_album_association(db, [photo_id], album_id, 'remove_from_album')
    if count == 0:
        raise HTTPException(status_code=404, detail="Photo not in album or not found")

    return crud.get_photo(db, photo_id)  # Return the photo