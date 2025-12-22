from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.face_service import face_service
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()

# 人脸检测结果的子模型（对应FaceResult）
class FaceResult(BaseModel):
    bbox: List[float]          # 人脸检测框 [x1, y1, x2, y2]
    kps: List[List[float]]     # 人脸关键点 [[x1,y1], [x2,y2], ...]
    det_score: float           # 检测置信度 0~1
    embedding: List[float]     # 人脸特征向量

# 接口响应模型
class RecognitionResponse(BaseModel):
    face_count: int            # 检测到的人脸数量
    faces: List[FaceResult]    # 每个人脸的详细结果

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
