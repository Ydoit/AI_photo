from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.face_service import face_service
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()

class FaceResult(BaseModel):
    bbox: List[float]
    kps: List[List[float]]
    det_score: float
    embedding: List[float]

class RecognitionResponse(BaseModel):
    face_count: int
    faces: List[FaceResult]

@router.post("/face-recognition", response_model=RecognitionResponse)
async def face_recognition(file: UploadFile = File(...)):
    """
    Upload an image file (JPG/PNG) to detect faces and extract features.
    """
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG and PNG are supported.")
    try:
        contents = await file.read()
        results = face_service.process_image(contents)
        return {
            "face_count": len(results),
            "faces": results
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
