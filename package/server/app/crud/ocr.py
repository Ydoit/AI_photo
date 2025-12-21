from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models.ocr import OCR
from app.schemas import ocr as schemas

def get_ocr_by_photo_id(db: Session, photo_id: UUID) -> List[OCR]:
    return db.query(OCR).filter(OCR.photo_id == photo_id).all()

def delete_ocr_by_photo_id(db: Session, photo_id: UUID) -> int:
    result = db.query(OCR).filter(OCR.photo_id == photo_id).delete()
    db.commit()
    return result
