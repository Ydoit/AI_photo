from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models.tag import PhotoTag, PhotoTagRelation
from app.schemas import tag as schemas
import uuid

def get_tag_by_name(db: Session, tag_name: str):
    return db.query(PhotoTag).filter(PhotoTag.tag_name == tag_name, PhotoTag.is_deleted == False).first()

def create_tag(db: Session, tag_name: str):
    db_tag = PhotoTag(tag_name=tag_name)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def get_photo_tags(db: Session, photo_id: UUID) -> List[schemas.PhotoTagResponse]:
    # Join PhotoTagRelation and PhotoTag
    results = db.query(PhotoTag, PhotoTagRelation.confidence)\
        .join(PhotoTagRelation, PhotoTag.id == PhotoTagRelation.tag_id)\
        .filter(PhotoTagRelation.photo_id == photo_id, PhotoTagRelation.is_deleted == False)\
        .all()
    
    tags = []
    for tag, confidence in results:
        tags.append(schemas.PhotoTagResponse(
            id=tag.id,
            tag_name=tag.tag_name,
            confidence=confidence
        ))
    return tags

def add_tag_to_photo(db: Session, photo_id: UUID, tag_name: str, confidence: float = 1.0) -> schemas.PhotoTagResponse:
    # Check if tag exists
    tag = get_tag_by_name(db, tag_name)
    if not tag:
        tag = create_tag(db, tag_name)
    
    # Check if relation exists
    relation = db.query(PhotoTagRelation).filter(
        PhotoTagRelation.photo_id == photo_id,
        PhotoTagRelation.tag_id == tag.id
    ).first()
    
    if relation:
        if relation.is_deleted:
            relation.is_deleted = False
            relation.confidence = confidence
            db.commit()
        else:
            # If manually added (confidence=1.0), overwrite existing confidence
            # Or if new confidence > old confidence (optional logic, but let's stick to simple override if manual)
            if confidence == 1.0:
                relation.confidence = 1.0
                db.commit()
        db.refresh(relation)
    else:
        relation = PhotoTagRelation(photo_id=photo_id, tag_id=tag.id, confidence=confidence)
        db.add(relation)
        db.commit()
        db.refresh(relation)
    
    return schemas.PhotoTagResponse(id=tag.id, tag_name=tag.tag_name, confidence=relation.confidence)

def remove_tag_from_photo(db: Session, photo_id: UUID, tag_id: UUID):
    relation = db.query(PhotoTagRelation).filter(
        PhotoTagRelation.photo_id == photo_id,
        PhotoTagRelation.tag_id == tag_id
    ).first()
    
    if relation:
        db.delete(relation)
        db.commit()
    return True
