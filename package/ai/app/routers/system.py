from fastapi import APIRouter
from app.config import settings

router = APIRouter()

@router.get("/health-check")
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}

@router.get("/version")
async def version():
    return {"version": settings.APP_VERSION}
