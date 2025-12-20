from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models.face import Face, FaceIdentity
from app.db.models.photo import Photo
from app.schemas import face as schemas
from app.core.config_manager import config_manager
import logging

logger = logging.getLogger(__name__)

# Face Operations
def create_face(db: Session, obj_in: schemas.FaceCreate) -> Face:
    db_obj = Face(
        photo_id=obj_in.photo_id,
        face_identity_id=obj_in.face_identity_id,
        face_rect=obj_in.face_rect,
        face_confidence=obj_in.face_confidence,
        recognize_confidence=obj_in.recognize_confidence,
        face_feature=obj_in.face_feature
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_face(db: Session, face_id: int) -> Optional[Face]:
    return db.query(Face).filter(Face.id == face_id, Face.is_deleted == False).first()

def get_faces(db: Session, skip: int = 0, limit: int = 100) -> List[Face]:
    return db.query(Face).filter(Face.is_deleted == False).offset(skip).limit(limit).all()

def update_face(db: Session, face_id: int, obj_in: schemas.FaceUpdate) -> Optional[Face]:
    db_obj = get_face(db, face_id)
    if not db_obj:
        return None
    
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_face(db: Session, face_id: int) -> Optional[Face]:
    """
    Delete a face record.
    Fix: When deleting a face, check if it is the default face for its identity.
    If so, try to find another face to set as default.
    """
    face = get_face(db, face_id)
    if not face:
        return None
    
    handle_face_deletion_dependency(db, face)
    
    db.delete(face)
    db.commit()
    return face

def handle_face_deletion_dependency(db: Session, face: Face):
    """
    Check if the face is the default face for its identity.
    If so, update the identity's default_face_id to another face.
    """
    if face.face_identity_id:
        identity = db.query(FaceIdentity).get(face.face_identity_id)
        if identity and identity.default_face_id == face.id:
            # Find another face for this identity
            # Exclude the current face and deleted faces
            next_face = db.query(Face).filter(
                Face.face_identity_id == identity.id,
                Face.id != face.id,
                Face.is_deleted == False
            ).order_by(Face.create_time.desc()).first()
            
            if next_face:
                identity.default_face_id = next_face.id
                logger.info(f"Updated default_face_id for identity {identity.id} to {next_face.id} (was {face.id})")
            else:
                # No other faces, set to None
                identity.default_face_id = None
                logger.info(f"Set default_face_id for identity {identity.id} to None (was {face.id})")
            
            db.add(identity)
            # Commit is handled by caller or we can flush here
            db.flush()

# FaceIdentity Operations
def create_identity(db: Session, obj_in: schemas.FaceIdentityCreate) -> FaceIdentity:
    db_obj = FaceIdentity(
        identity_name=obj_in.identity_name
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_identity(db: Session, identity_id: UUID) -> Optional[FaceIdentity]:
    return db.query(FaceIdentity).filter(FaceIdentity.id == identity_id, FaceIdentity.is_deleted == False).first()

def get_identities(db: Session, skip: int = 0, limit: int = 100) -> List[FaceIdentity]:
    return db.query(FaceIdentity).filter(FaceIdentity.is_deleted == False).offset(skip).limit(limit).all()

def update_identity(db: Session, identity_id: UUID, obj_in: schemas.FaceIdentityUpdate) -> Optional[FaceIdentity]:
    db_obj = get_identity(db, identity_id)
    if not db_obj:
        return None
    
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_identity(db: Session, identity_id: UUID) -> bool:
    identity = get_identity(db, identity_id)
    if not identity:
        return False
    
    # Dissociate faces
    faces = db.query(Face).filter(Face.face_identity_id == identity_id).all()
    for face in faces:
        face.face_identity_id = None
        db.add(face)
    
    identity.is_deleted = True
    db.add(identity)
    db.commit()
    return True

# Advanced Query Operations
def get_identities_with_details(
    db: Session, 
    skip: int = 0, 
    limit: int = 20, 
    min_photos: int = 0
) -> List[dict]:
    # Subquery for face counts
    face_counts = db.query(
        Face.face_identity_id,
        func.count(Face.id).label("count")
    ).filter(
        Face.is_deleted == False,
        Face.face_identity_id != None
    ).group_by(Face.face_identity_id).subquery()

    # Main query
    query = db.query(
        FaceIdentity,
        face_counts.c.count,
        Face,
        Photo
    ).outerjoin(
        face_counts, FaceIdentity.id == face_counts.c.face_identity_id
    ).outerjoin(
        Face, FaceIdentity.default_face_id == Face.id
    ).outerjoin(
        Photo, Face.photo_id == Photo.id
    ).filter(
        FaceIdentity.is_deleted == False
    ).order_by(
        FaceIdentity.create_time.desc()
    ).offset(skip).limit(limit)

    results = []
    
    p_size = config_manager.config.image.preview_size

    for identity, count, default_face, photo in query.all():
        if not count or count <= min_photos:
            continue
        
        cover = None
        if default_face and photo:
            scale = p_size / max(photo.width, photo.height) if max(photo.width, photo.height) > 0 else 1
            cover = schemas.CoverPhotoInfo(
                photo_id=default_face.photo_id,
                width=int(photo.width * scale),
                height=int(photo.height * scale),
                face_rect=default_face.face_rect
            )
            
        results.append({
            "id": identity.id,
            "identity_name": identity.identity_name,
            "default_face_id": identity.default_face_id,
            "face_count": count or 0,
            "cover_photo": cover,
            "create_time": identity.create_time,
            "update_time": identity.update_time
        })
    return results

def get_identity_photos(db: Session, identity_id: UUID, skip: int = 0, limit: int = 50) -> List[Photo]:
    return db.query(Photo).join(Face).filter(
        Face.face_identity_id == identity_id,
        Photo.id == Face.photo_id,
        Face.is_deleted == False
    ).offset(skip).limit(limit).all()

def remove_photos_from_identity(db: Session, identity_id: UUID, photo_ids: List[UUID]) -> int:
    identity = get_identity(db, identity_id)
    if not identity:
        return 0
    
    faces = db.query(Face).filter(
        Face.face_identity_id == identity_id,
        Face.photo_id.in_(photo_ids)
    ).all()
    
    for face in faces:
        handle_face_deletion_dependency(db, face)
        face.face_identity_id = None
        db.add(face)
        
    db.commit()
    return len(faces)

def delete_faces_by_photo(db: Session, photo_id: UUID) -> int:
    faces = db.query(Face).filter(Face.photo_id == photo_id).all()
    count = len(faces)
    for face in faces:
        handle_face_deletion_dependency(db, face)
        db.delete(face)
    db.commit()
    return count

def set_identity_cover(db: Session, identity_id: UUID, photo_id: UUID) -> bool:
    identity = get_identity(db, identity_id)
    if not identity:
        return False
        
    face = db.query(Face).filter(
        Face.face_identity_id == identity_id,
        Face.photo_id == photo_id
    ).first()
    
    if not face:
        return False
        
    identity.default_face_id = face.id
    db.add(identity)
    db.commit()
    return True

def merge_identities(db: Session, target_id: UUID, source_ids: List[UUID]) -> bool:
    target = get_identity(db, target_id)
    if not target:
        return False
         
    for source_id in source_ids:
        if source_id == target_id:
            continue
            
        source = get_identity(db, source_id)
        if not source:
            continue
            
        # Move faces
        faces = db.query(Face).filter(Face.face_identity_id == source_id).all()
        for face in faces:
            face.face_identity_id = target_id
            db.add(face)
            
        # Soft delete source
        source.is_deleted = True
        db.add(source)
        
    db.commit()
    return True
