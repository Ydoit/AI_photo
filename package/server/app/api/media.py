import os
import shutil
import uuid
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status, Form, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse, Response
from sqlalchemy.orm import Session

from app.crud.album import save_and_create_photo
from app.dependencies import get_db
from app.db.models.photo import Photo
from app.service import storage
from app.service.storage import _get_storage_root
from app.crud import album as crud_album
from app.crud import face as crud_face

from app.schemas import photo as schemas

router = APIRouter()

def _get_thumbnail_path(photo_id: UUID, db: Session, size: str = 'small') -> str:
    compact = str(photo_id).replace('-', '')
    p1, p2 = compact[:2], compact[2:4]
    root = _get_storage_root(db)
    base = os.path.join(root, 'thumbnails', p1, p2)
    
    if size == 'small':
        return os.path.join(base, f"{compact}-thumb.jpg")
    return os.path.join(base, f"{compact}.jpg")

@router.get('/{photo_id}/thumbnail')
def get_thumbnail(photo_id: UUID, size: str = 'small', db: Session = Depends(get_db)):
    path = _get_thumbnail_path(photo_id, db, size)
    if not os.path.exists(path):
        # Fallback if thumbnail not found: try to return original if it's an image?
        # Or return 404. For now 404.
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
    file_size = os.path.getsize(file_path)
    
    # Determine media type
    ext = os.path.splitext(file_path)[1].lower()
    media_type = "application/octet-stream"
    if ext in ('.png', '.jpg', '.jpeg', '.webp'):
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
        db_album = crud_album.get_album(db, album_id=album_id)
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