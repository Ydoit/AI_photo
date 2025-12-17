from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.dependencies import get_db
from app.db.models.face import FaceIdentity, Face
from app.db.models.photo import Photo
from app.schemas import album
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

router = APIRouter()

class FaceIdentitySchema(BaseModel):
    id: UUID
    identity_name: Optional[str]
    default_face_id: Optional[int]
    face_count: Optional[int]
    cover_photo: Optional[str] # URL or ID

    class Config:
        from_attributes = True

class FaceIdentityUpdate(BaseModel):
    name: str

class MergeRequest(BaseModel):
    source_ids: List[UUID]
    target_id: UUID

class RemovePhotosRequest(BaseModel):
    photo_ids: List[UUID]

class SetCoverRequest(BaseModel):
    photo_id: UUID

@router.get("/identities", response_model=List[FaceIdentitySchema])
def list_identities(page: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    offset = (page - 1) * limit
    identities = db.query(FaceIdentity).filter(FaceIdentity.is_deleted == False)\
        .order_by(FaceIdentity.create_time.desc())\
        .offset(offset).limit(limit).all()
    
    results = []
    for identity in identities:
        # Count faces
        count = db.query(Face).filter(Face.face_identity_id == identity.id, Face.is_deleted == False).count()
        # Get cover photo (from default face)
        cover = None
        if identity.default_face_id:
            face = db.query(Face).get(identity.default_face_id)
            if face and face.photo:
                 # Construct a thumbnail URL or return photo ID
                 # Assuming photo.file_path or similar. 
                 # Let's return a simple structure the frontend can use to fetch the image.
                 # Ideally we return a thumbnail URL.
                 # We'll use the existing /api/photos/{id}/thumbnail endpoint convention
                 cover = str(face.photo.id) 
        
        results.append({
            "id": identity.id,
            "identity_name": identity.identity_name,
            "default_face_id": identity.default_face_id,
            "face_count": count,
            "cover_photo": cover
        })
    return results


@router.get("/identities/{id}/photos", response_model=List[album.Photo])
def get_identity_photos(id: UUID, page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    offset = (page - 1) * limit
    # Join Face and Photo
    # We want distinct photos
    photos = db.query(Photo).join(Face).filter(
        Face.face_identity_id == id,
        Photo.id == Face.photo_id
    ).offset(offset).limit(limit).all()

    # Use existing Photo schema or return simplified
    return photos

@router.delete("/identities/{id}")
def delete_identity(id: UUID, db: Session = Depends(get_db)):
    identity = db.query(FaceIdentity).get(id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    # Soft delete
    identity.is_deleted = True
    # Also unassign faces? Or keep them linked to a deleted identity?
    # Usually we unassign or mark faces as deleted?
    # User said "Soft delete person record". 
    # If we just soft delete the identity, the faces still point to it.
    # Let's unassign faces so they can be re-clustered?
    # Or just mark identity as deleted.
    # Let's keep it simple: soft delete identity.
    # But maybe we should set faces to NULL identity so they go back to 'unknown'?
    # Let's assume we keep them linked but hidden.
    
    db.commit()
    return {"status": "success"}

@router.post("/identities/{id}/remove-photos")
def remove_photos_from_identity(id: UUID, payload: RemovePhotosRequest, db: Session = Depends(get_db)):
    identity = db.query(FaceIdentity).get(id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
        
    # Find faces in these photos that belong to this identity
    faces = db.query(Face).filter(
        Face.face_identity_id == id,
        Face.photo_id.in_(payload.photo_ids)
    ).all()
    
    for face in faces:
        face.face_identity_id = None # Dissociate
        
    db.commit()
    return {"status": "success", "count": len(faces)}

@router.put("/identities/{id}/cover")
def set_identity_cover(id: UUID, payload: SetCoverRequest, db: Session = Depends(get_db)):
    identity = db.query(FaceIdentity).get(id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
        
    # Find face in the photo belonging to this identity
    face = db.query(Face).filter(
        Face.face_identity_id == id,
        Face.photo_id == payload.photo_id
    ).first()
    
    if not face:
        raise HTTPException(status_code=404, detail="Face not found in this photo for this identity")
        
    identity.default_face_id = face.id
    db.commit()
    return {"status": "success"}

@router.put("/identities/{id}/name")
def rename_identity(id: UUID, payload: FaceIdentityUpdate, db: Session = Depends(get_db)):
    identity = db.query(FaceIdentity).get(id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    identity.identity_name = payload.name
    db.commit()
    return {"status": "success", "name": payload.name}

@router.post("/identities/merge")
def merge_identities(payload: MergeRequest, db: Session = Depends(get_db)):
    target = db.query(FaceIdentity).get(payload.target_id)
    if not target:
         raise HTTPException(status_code=404, detail="Target identity not found")
         
    for source_id in payload.source_ids:
        if source_id == payload.target_id:
            continue
            
        source = db.query(FaceIdentity).get(source_id)
        if not source:
            continue
            
        # Move faces
        faces = db.query(Face).filter(Face.face_identity_id == source_id).all()
        for face in faces:
            face.face_identity_id = payload.target_id
            
        # Soft delete source
        source.is_deleted = True
        
    db.commit()
    return {"status": "success"}
