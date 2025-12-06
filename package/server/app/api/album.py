from typing import List, Optional, Dict, Any
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
from datetime import datetime
import re
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import json

router = APIRouter()

# Helper Functions for Metadata

def _convert_to_degrees(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to degress in float format
    """
    def _to_float(v):
        if isinstance(v, (tuple, list)) and len(v) == 2:
            # Handle (numerator, denominator) tuple
            if v[1] == 0:
                return 0.0
            return float(v[0]) / float(v[1])
        try:
            # Handle IFDRational or simple numbers
            return float(v)
        except (TypeError, ValueError):
            # Fallback for IFDRational in some PIL versions if it doesn't cast directly
            if hasattr(v, 'numerator') and hasattr(v, 'denominator'):
                 if v.denominator == 0:
                     return 0.0
                 return float(v.numerator) / float(v.denominator)
            return 0.0

    d = _to_float(value[0])
    m = _to_float(value[1])
    s = _to_float(value[2])
    return d + (m / 60.0) + (s / 3600.0)

def get_gps_info(exif_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
    if 'GPSInfo' not in exif_data:
        return None
    
    gps_info = exif_data['GPSInfo']
    
    lat = None
    lng = None
    
    if 'GPSLatitude' in gps_info and 'GPSLatitudeRef' in gps_info:
        lat = _convert_to_degrees(gps_info['GPSLatitude'])
        if gps_info['GPSLatitudeRef'] != 'N':
            lat = -lat
            
    if 'GPSLongitude' in gps_info and 'GPSLongitudeRef' in gps_info:
        lng = _convert_to_degrees(gps_info['GPSLongitude'])
        if gps_info['GPSLongitudeRef'] != 'E':
            lng = -lng
            
    if lat is not None and lng is not None:
        return {"latitude": lat, "longitude": lng}
    return None

def get_exif_data(image: Image.Image) -> Dict[str, Any]:
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]
                exif_data[decoded] = gps_data
            else:
                # Filter out binary data or non-serializable stuff if needed
                if isinstance(value, (bytes, bytearray)):
                     try:
                         exif_data[decoded] = value.decode()
                     except:
                         exif_data[decoded] = str(value)
                else:
                     exif_data[decoded] = value
    return exif_data

def extract_metadata(file_path: str, filename: str) -> Dict[str, Any]:
    """
    Extracts photo_time, exif_info, and location from the file.
    Priority:
    1. EXIF DateTimeOriginal
    2. Filename (YYYYMMDD_HHMMSS or YYYYMMDD)
    3. Current Time
    """
    metadata = {
        "photo_time": None,
        "exif_info": None,
        "location": None
    }
    
    # 1. Try EXIF
    try:
        if file_path.lower().endswith(('.jpg', '.jpeg', '.tiff', '.webp')):
            with Image.open(file_path) as img:
                # Extract full EXIF
                exif_dict = get_exif_data(img)
                if exif_dict:
                    # Serialize for storage
                    # Convert non-serializable objects to string
                    def default_serializer(obj):
                        if isinstance(obj, (bytes, bytearray)):
                            return str(obj)
                        return str(obj)
                    
                    metadata["exif_info"] = json.dumps(exif_dict, default=default_serializer, ensure_ascii=False)
                    
                    # Extract Date (DateTimeOriginal)
                    date_str = exif_dict.get("DateTimeOriginal")
                    if date_str:
                        try:
                            metadata["photo_time"] = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                        except ValueError:
                            pass
                    
                    # Extract GPS
                    metadata["location"] = get_gps_info(exif_dict)

    except Exception as e:
        print(f"Error extracting metadata: {e}")
    
    # 2. If photo_time is still None, try Filename
    if metadata["photo_time"] is None:
        try:
            match = re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', filename)
            if match:
                metadata["photo_time"] = datetime(*map(int, match.groups()))
            else:
                match = re.search(r'(\d{4})(\d{2})(\d{2})', filename)
                if match:
                    metadata["photo_time"] = datetime(*map(int, match.groups()))
        except Exception:
            pass
            
    # 3. Fallback to current time
    if metadata["photo_time"] is None:
        metadata["photo_time"] = datetime.now()

    return metadata

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
    
    extracted_meta = extract_metadata(file_path, file_name)
    
    # Create Schema for DB
    photo_create = schemas.PhotoCreate(
        file_type=file_type,
        size=size,
        width=width,
        height=height,
        filename=file_name,
        photo_time=extracted_meta["photo_time"]
    )
    
    # Create Metadata Schema
    metadata_create = schemas.PhotoMetadataCreate(
        exif_info=extracted_meta["exif_info"],
        location=extracted_meta["location"]
    )
    
    return crud.create_photo(db, photo_create, album_id, file_path, photo_id=photo_id, metadata=metadata_create)

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

    # Generate ID
    photo_id = uuid.uuid4()
    
    # Save file
    file_path = storage.save_upload_file(file, photo_id)
    
    # Create and Save
    return _save_and_create_photo(db, file_path, file.filename, album_id, photo_id)

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
    # Remove association
    count = crud.batch_update_album_association(db, [photo_id], album_id, 'remove_from_album')
    if count == 0:
        raise HTTPException(status_code=404, detail="Photo not in album or not found")
    
    return crud.get_photo(db, photo_id) # Return the photo

@router.delete("/photos/{photo_id}", response_model=schemas.Photo)
def delete_photo_global(photo_id: UUID, db: Session = Depends(get_db)):
    db_photo = crud.delete_photo(db, photo_id=photo_id)
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Delete file from storage
    storage.delete_file(db_photo.file_path, db_photo.id)
    
    return db_photo

@router.put("/photos/{photo_id}", response_model=schemas.Photo)
def update_photo(photo_id: UUID, photo: schemas.PhotoUpdate, db: Session = Depends(get_db)):
    db_photo = crud.update_photo(db, photo_id, photo)
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return db_photo

# Metadata Endpoints

@router.get("/photos/{photo_id}/metadata", response_model=schemas.PhotoMetadata)
def read_photo_metadata(photo_id: UUID, db: Session = Depends(get_db)):
    # Ignoring album_id for metadata retrieval as it's global
    db_metadata = crud.get_photo_metadata(db, photo_id=photo_id)
    if not db_metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")
    return db_metadata

@router.put("/photos/{photo_id}/metadata", response_model=schemas.PhotoMetadata)
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
    final_path = os.path.join(storage.UPLOAD_DIR, f"{photo_id}{ext}")
    
    with open(final_path, "wb") as outfile:
        for chunk_idx in chunks:
            chunk_path = os.path.join(chunk_dir, str(chunk_idx))
            with open(chunk_path, "rb") as infile:
                outfile.write(infile.read())
    
    # Clean up chunks
    shutil.rmtree(chunk_dir)

    return _save_and_create_photo(db, final_path, file_name, album_id, photo_id)