from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.crud import album as crud
from app.schemas import album as schemas
from app.service import storage
from app.db.models.photo import FileType
import uuid
import os
import shutil

router = APIRouter()

# Helper Function
def _save_and_create_photo(db: Session, file_path: str, file_name: str, album_id: Optional[UUID], photo_id: UUID):
    # Determine file type
    ext = os.path.splitext(file_name)[1]
    file_type = FileType.image
    if ext.lower() in ['.mp4', '.mov', '.avi']:
        file_type = FileType.video
    
    # Generate thumbnail
    storage.generate_thumbnail(file_path, photo_id)
    
    # Get Metadata
    size = storage.get_file_size(file_path)
    width, height = storage.get_image_dimensions(file_path)
    
    # Create Schema for DB
    photo_create = schemas.PhotoCreate(
        file_type=file_type,
        size=size,
        width=width,
        height=height
    )
    
    return crud.create_photo(db, photo_create, album_id, file_path, photo_id=photo_id)

# Album Endpoints

@router.post("/albums", response_model=schemas.Album)
def create_album(album: schemas.AlbumCreate, db: Session = Depends(get_db)):
    return crud.create_album(db=db, album=album)

@router.get("/albums", response_model=List[schemas.Album])
def read_albums(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_albums(db, skip=skip, limit=limit)

@router.get("/albums/{album_id}", response_model=schemas.Album)
def read_album(album_id: UUID, db: Session = Depends(get_db)):
    db_album = crud.get_album(db, album_id=album_id)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    return db_album

@router.delete("/albums/{album_id}", response_model=schemas.Album)
def delete_album(album_id: UUID, db: Session = Depends(get_db)):
    db_album = crud.delete_album(db, album_id=album_id)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    return db_album

@router.put("/albums/{album_id}", response_model=schemas.Album)
def update_album(album_id: UUID, album: schemas.AlbumCreate, db: Session = Depends(get_db)):
    db_album = crud.update_album(db, album_id=album_id, album=album)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    return db_album

# Photo Endpoints

@router.get("/photos", response_model=List[schemas.Photo])
def read_all_photos(
    skip: int = 0, 
    limit: int = 100, 
    year: Optional[str] = None,
    city: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return crud.get_all_photos(db, skip=skip, limit=limit, year=year, city=city, tag=tag)

@router.post("/photos/batch")
def batch_update_photos(
    batch_data: schemas.BatchPhotoUpdate,
    db: Session = Depends(get_db)
):
    if batch_data.action == 'move_to_album':
        if batch_data.target_album_id:
             # Verify album exists
            db_album = crud.get_album(db, album_id=batch_data.target_album_id)
            if not db_album:
                raise HTTPException(status_code=404, detail="Target album not found")
        crud.batch_update_album_id(db, batch_data.photo_ids, batch_data.target_album_id)
        return {"message": "Photos moved successfully"}
    
    elif batch_data.action == 'delete':
        # Get photos to delete files
        photos = crud.get_photos_by_ids(db, batch_data.photo_ids)
        for photo in photos:
            storage.delete_file(photo.file_path, photo.id)
            
        crud.batch_delete_photos_db(db, batch_data.photo_ids)
        return {"message": "Photos deleted successfully"}
        
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@router.post("/photos", response_model=schemas.Photo)
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

    # Determine file type
    content_type = file.content_type
    file_type = FileType.image
    if content_type.startswith('video'):
        file_type = FileType.video
    
    # Generate ID
    photo_id = uuid.uuid4()
    
    # Save file
    file_path = storage.save_upload_file(file, photo_id)
    
    # Generate thumbnail
    storage.generate_thumbnail(file_path, photo_id)
    
    # Get Metadata
    size = storage.get_file_size(file_path)
    width, height = storage.get_image_dimensions(file_path)
    
    # Create Schema for DB
    photo_create = schemas.PhotoCreate(
        file_type=file_type,
        size=size,
        width=width,
        height=height
    )
    
    db_photo = crud.create_photo(db, photo_create, album_id, file_path, photo_id=photo_id)
    
    return db_photo

@router.post("/albums/{album_id}/photos", response_model=schemas.Photo)
async def upload_photo(
    album_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Forward to generic handler
    return await upload_photo_generic(album_id, file, db)

@router.get("/albums/{album_id}/photos", response_model=List[schemas.Photo])
def read_photos(album_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_photos(db, album_id=album_id, skip=skip, limit=limit)

@router.delete("/albums/{album_id}/photos/{photo_id}", response_model=schemas.Photo)
def delete_photo(album_id: UUID, photo_id: UUID, db: Session = Depends(get_db)):
    db_photo = crud.delete_photo(db, photo_id=photo_id)
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Delete file from storage
    storage.delete_file(db_photo.file_path, db_photo.id)
    
    return db_photo

# Metadata Endpoints

@router.get("/albums/{album_id}/photos/{photo_id}/metadata", response_model=schemas.PhotoMetadata)
def read_photo_metadata(album_id: UUID, photo_id: UUID, db: Session = Depends(get_db)):
    db_metadata = crud.get_photo_metadata(db, photo_id=photo_id)
    if not db_metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")
    return db_metadata

@router.put("/albums/{album_id}/photos/{photo_id}/metadata", response_model=schemas.PhotoMetadata)
def update_photo_metadata(
    album_id: UUID,
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
    # Use storage service helper if possible, but here we are merging manually
    final_path = os.path.join(storage.UPLOAD_DIR, f"{photo_id}{ext}")
    
    with open(final_path, "wb") as outfile:
        for chunk_idx in chunks:
            chunk_path = os.path.join(chunk_dir, str(chunk_idx))
            with open(chunk_path, "rb") as infile:
                outfile.write(infile.read())
    
    # Clean up chunks
    shutil.rmtree(chunk_dir)
    
    # Determine file type
    file_type = FileType.image
    # Check extension
    if ext.lower() in ['.mp4', '.mov', '.avi']:
        file_type = FileType.video
    elif ext.lower() in ['.heic', '.jpg', '.jpeg', '.png']:
        file_type = FileType.image # Live photo logic omitted for simplicity
        
    # Generate thumbnail
    storage.generate_thumbnail(final_path, photo_id)
    
    # Get Metadata
    size = storage.get_file_size(final_path)
    width, height = storage.get_image_dimensions(final_path)
    
    # Create Schema for DB
    photo_create = schemas.PhotoCreate(
        file_type=file_type,
        size=size,
        width=width,
        height=height
    )
    
    db_photo = crud.create_photo(db, photo_create, album_id, final_path, photo_id=photo_id)
    
    return db_photo

@router.post("/upload/finish/{album_id}", response_model=schemas.Photo)
def finish_upload(
    album_id: UUID,
    upload_id: UUID = Form(...),
    file_name: str = Form(...),
    db: Session = Depends(get_db)
):
    # Forward to generic handler
    return finish_upload_generic(upload_id=upload_id, file_name=file_name, album_id=album_id, db=db)
