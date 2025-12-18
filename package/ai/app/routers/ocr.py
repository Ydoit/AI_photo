from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ocr_service import ocr_service

router = APIRouter()

@router.post("/predict")
async def ocr_predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        results = ocr_service.detect_text(contents)
        return {"results": results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

