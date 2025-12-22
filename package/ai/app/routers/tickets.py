from fastapi import APIRouter

router = APIRouter()

@router.post("/tickets/predict")
async def ticket_predict():
    return {"message": "Ticket recognition service not implemented yet"}
