from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
import logging
import traceback

from app.services.ticket_service import ticket_service

router = APIRouter()

class TicketInfo(BaseModel):
    train_code: Optional[str] = Field(default=None)
    departure_station: Optional[str] = Field(default=None)
    arrival_station: Optional[str] = Field(default=None)
    datetime: Optional[str] = Field(default=None)
    carriage: Optional[str] = Field(default=None)
    seat_num: Optional[str] = Field(default=None)
    berth_type: Optional[str] = Field(default=None)
    price: Optional[str] = Field(default=None)
    seat_type: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    discount_type: Optional[str] = Field(default=None)
    
    # 飞机票特有字段 (兼容)
    flight_code: Optional[str] = Field(default=None)
    departure_city: Optional[str] = Field(default=None)
    arrival_city: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default="train")
    
    detection_id: int = 0

class TicketRecognitionResponse(BaseModel):
    ticket_count: int
    tickets: List[TicketInfo]

@router.post("/predict", response_model=TicketRecognitionResponse)
async def predict_ticket(file: UploadFile = File(...)):
    """
    Upload an image file (JPG/PNG) to recognize train tickets.
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG and PNG are supported.")
    
    try:
        contents = await file.read()
        results = ticket_service.detect(contents)
        return {
            "ticket_count": results["count"],
            "tickets": results["tickets"]
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/predict-batch")
async def predict_tickets_batch(files: List[UploadFile] = File(...)):
    """
    Upload multiple images to recognize tickets.
    """
    results_list = []
    for file in files:
        try:
            contents = await file.read()
            res = ticket_service.detect(contents)
            results_list.append({
                "filename": file.filename,
                "success": True,
                "data": res
            })
        except Exception as e:
            logging.error(f"Error processing {file.filename}: {e}")
            results_list.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    return {"results": results_list}
