from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

class OCRBase(BaseModel):
    text: str
    text_score: float
    polygon: List[List[float]] # [[x1, y1], [x2, y2], ...] normalized 0-1

class OCRCreate(OCRBase):
    photo_id: UUID

class OCR(OCRBase):
    id: int
    photo_id: UUID

    class Config:
        from_attributes = True

class OCRResponse(BaseModel):
    count: int
    records: List[OCR]
