import uvicorn
from fastapi import FastAPI
from app.config import settings
from app.routers import system, face, ocr, object_detection, tickets

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Microservice for AI capabilities including Face Recognition, OCR, etc."
)

# Include Routers
app.include_router(system.router, tags=["System"])
app.include_router(face.router, tags=["Face Recognition"])
app.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
app.include_router(object_detection.router, prefix="/object-detection", tags=["Object Detection"])
app.include_router(tickets.router, prefix="/tickets", tags=["Ticket Recognition"])

if __name__ == "__main__":
    # docs：http://localhost:8001/docs
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
