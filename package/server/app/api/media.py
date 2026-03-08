import json
import os
import shutil
import uuid
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status, Form, UploadFile, File, Query
from fastapi.responses import FileResponse, StreamingResponse, Response
from sqlalchemy.orm import Session

from app.crud.photo import save_and_create_photo
from app.db.models.task import TaskType
from app.dependencies import get_db
from app.db.models.photo import Photo
from app.service import storage
from app.service.storage import _get_storage_root
from app.crud import album as crud_album
from app.crud import face as crud_face

from app.schemas import photo as schemas
from app.service.task_manager import TaskManager
from app.api.deps import get_current_user
from app.db.models.user import User

router = APIRouter()

def _get_thumbnail_path(user_id: UUID, photo_id: UUID, db: Session, size: str = 'small') -> str:
    compact = str(photo_id).replace('-', '')
    p1, p2 = compact[:2], compact[2:4]
    root = _get_storage_root(user_id, db)
    base = os.path.join(root, 'thumbnails', p1, p2)
    
    if size == 'small':
        return os.path.join(base, f"{compact}-thumb.jpg")
    return os.path.join(base, f"{compact}.jpg")

@router.get('/{photo_id}/video')
def get_live_photo_video(
    photo_id: UUID,
    request: Request,
    range: str = Header(None),
    db: Session = Depends(get_db)
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Video file not found")

    ext = os.path.splitext(photo.file_path)[1].lower()
    if ext in ('.jpg', 'jpeg'):
        file_path = photo.file_path[:-3] + 'mp4'
        if not os.path.exists(file_path):
            file_path = _get_thumbnail_path(photo.owner_id, photo_id, db, 'medium')[:-4] + '.mp4'
    else:
        file_path = photo.file_path[:-4] + 'MOV'
    file_size = os.path.getsize(file_path)

    # Determine media type (usually mp4 or mov)
    ext = os.path.splitext(file_path)[1].lower()
    media_type = f"video/{ext.lstrip('.')}"
    if ext == '.mov': media_type = "video/quicktime"

    # Handle Range header
    if range:
        try:
            start, end = range.replace("bytes=", "").split("-")
            start = int(start)
            end = int(end) if end else file_size - 1
            
            if start >= file_size:
                 # Requesting past end of file
                 headers = {"Content-Range": f"bytes */{file_size}"}
                 return Response(status_code=416, headers=headers)

            chunk_size = end - start + 1

            def iterfile():
                with open(file_path, "rb") as f:
                    f.seek(start)
                    bytes_read = 0
                    while bytes_read < chunk_size:
                        chunk = f.read(min(4096, chunk_size - bytes_read))
                        if not chunk:
                            break
                        bytes_read += len(chunk)
                        yield chunk
            
            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Content-Type": media_type,
            }
            
            return StreamingResponse(iterfile(), status_code=206, headers=headers, media_type=media_type)
        except ValueError:
            pass # Fallback to full content if range parse fails

    # Full content
    return FileResponse(file_path, media_type=media_type, headers={"Accept-Ranges": "bytes", "Cache-Control": "public, max-age=31536000"})

@router.get('/{photo_id}/thumbnail')
def get_thumbnail(photo_id: UUID, size: str = 'small', db: Session = Depends(get_db)):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    path = _get_thumbnail_path(photo.owner_id, photo_id, db, size)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=31536000"})

@router.get('/{photo_id}/file')
def get_media_file(
    photo_id: UUID,
    request: Request,
    range: str = Header(None),
    db: Session = Depends(get_db)
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo or not os.path.exists(photo.file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    file_path = photo.file_path
    # Determine media type
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.heic':
        file_path = _get_thumbnail_path(photo.owner_id, photo_id, db, 'medium')
    file_size = os.path.getsize(file_path)

    media_type = "application/octet-stream"
    if ext in ('.png', '.jpg', '.jpeg', '.webp', '.tiff', '.gif'):
        media_type = f"image/{ext.lstrip('.')}"
        if ext == '.jpg': media_type = "image/jpeg"
    elif ext in ('.mp4', '.mov', '.avi', '.mkv', '.webm'):
        media_type = f"video/{ext.lstrip('.')}"
        if ext == '.mov': media_type = "video/quicktime"
        if ext == '.mkv': media_type = "video/x-matroska"

    # Handle Range header
    if range:
        try:
            start, end = range.replace("bytes=", "").split("-")
            start = int(start)
            end = int(end) if end else file_size - 1
            
            if start >= file_size:
                 # Requesting past end of file
                 headers = {"Content-Range": f"bytes */{file_size}"}
                 return Response(status_code=416, headers=headers)

            chunk_size = end - start + 1

            def iterfile():
                with open(file_path, "rb") as f:
                    f.seek(start)
                    bytes_read = 0
                    while bytes_read < chunk_size:
                        chunk = f.read(min(4096, chunk_size - bytes_read))
                        if not chunk:
                            break
                        bytes_read += len(chunk)
                        yield chunk
            
            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Content-Type": media_type,
            }
            
            return StreamingResponse(iterfile(), status_code=206, headers=headers, media_type=media_type)
        except ValueError:
            pass # Fallback to full content if range parse fails

    # Full content
    return FileResponse(file_path, media_type=media_type, headers={"Accept-Ranges": "bytes", "Cache-Control": "public, max-age=31536000"})

def add_tasks(db: Session, user_id: UUID, photo_id: UUID, file_path: str):
    TaskManager.get_instance().add_tasks(db, [
        {
            'type': TaskType.EXTRACT_METADATA,
            'payload': {'photo_id': str(photo_id), 'file_path': file_path, 'user_id': str(user_id)}
        },
        {
            'type': TaskType.RECOGNIZE_FACE,
            'payload': {'photo_id': str(photo_id), 'file_path': file_path, 'user_id': str(user_id)}
        },
        {
            'type': TaskType.OCR,
            'payload': {'photo_id': str(photo_id), 'file_path': file_path, 'user_id': str(user_id)}
        },
        {
            'type': TaskType.RECOGNIZE_TICKET,
            'payload': {'photo_id': str(photo_id), 'file_path': file_path, 'user_id': str(user_id)}
        },
        {
            'type': TaskType.CLASSIFY_IMAGE,
            'payload': {'photo_id': str(photo_id), 'file_path': file_path, 'user_id': str(user_id)}
        },
        {
            'type': TaskType.VISUAL_DESCRIPTION,
            'payload': {'photo_id': str(photo_id), 'file_path': file_path, 'user_id': str(user_id)}
        },
    ])

@router.post("", response_model=schemas.Photo)
async def upload_photo_generic(
        album_id: Optional[UUID] = Form(None),
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if album_id:
        # Verify album exists
        db_album = crud_album.get_album(db, album_id=album_id, user_id=current_user.id)
        if not db_album:
            raise HTTPException(status_code=404, detail="Album not found")

    # Generate ID
    photo_id = uuid.uuid4()
    # Save file
    file_path = storage.save_upload_file(file, photo_id, current_user.id)
    # Create and Save
    photo = save_and_create_photo(db, file_path, file.filename, album_id, photo_id, user_id=current_user.id)
    # Add tasks
    add_tasks(db, current_user.id, photo_id, file_path)

    return photo

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
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if album_id:
        # Verify album exists
        db_album = crud_album.get_album(db, album_id=album_id, user_id=current_user.id)
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
        final_path = storage.save_upload_file(_Tmp, photo_id, current_user.id)

    # Clean up chunks
    shutil.rmtree(chunk_dir)

    # Create and Save
    photo = save_and_create_photo(db, final_path, file_name, album_id, photo_id, user_id=current_user.id)

    # Add tasks
    add_tasks(db, current_user.id, photo_id, final_path)

    return photo

@router.get('/geojson')
def get_geojson(level: str = Query("city")):
    if level not in ["province", "city", "district"]:
        raise HTTPException(status_code=400, detail="Invalid level. Must be province, city, or district.")
    try:
        level_cn = {"province": "省", "city": "市", "district": "县"}[level]
        path = os.path.join("resources","geo_data", f"中国_{level_cn}.geojson")
        return FileResponse(path, media_type="application/geo+json", headers={"Cache-Control": "public, max-age=31536000"})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"GeoJSON file for {level} not found.")

    return geojson
