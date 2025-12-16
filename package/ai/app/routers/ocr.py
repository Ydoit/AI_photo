from fastapi import APIRouter

router = APIRouter()

@router.post("/ocr/predict")
async def ocr_predict():
    return {"message": "OCR service not implemented yet"}
