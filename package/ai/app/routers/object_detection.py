from fastapi import APIRouter

router = APIRouter()

@router.post("/object-detection/predict")
async def object_detection_predict():
    return {"message": "Object detection service not implemented yet"}
