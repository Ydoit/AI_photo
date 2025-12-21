from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import logging
from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.core.logger import setup_logging

from app.api import (
    user, album, settings, index, media, stats, tasks, photo, face, ocr
)

app = FastAPI(title="TrailSnap - 足迹相册")

# Initialize logging listener
log_listener = None

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    operation = f"{request.method} {request.url.path}"
    params = dict(request.query_params)
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        extra = {
            "operation": operation,
            "params": params,
            "result": response.status_code,
            "duration_ms": f"{process_time:.2f}"
        }
        logging.getLogger("app.middleware").info("Request processed", extra=extra)
        
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        extra = {
            "operation": operation,
            "params": params,
            "result": "Error",
            "duration_ms": f"{process_time:.2f}"
        }
        logging.getLogger("app.middleware").error(f"Request failed: {str(e)}", exc_info=e, extra=extra)
        raise e

app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(photo.router, prefix="/photos", tags=["Photos"])
app.include_router(album.router,prefix="/albums", tags=["Albums"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
app.include_router(index.router, prefix="/index", tags=["Index"])
app.include_router(media.router, prefix="/media", tags=["Media"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(face.router, prefix="/faces", tags=["Faces"])
app.include_router(ocr.router, prefix="/ocr", tags=["OCR"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Image Manager Backend Ready"}

@app.on_event("startup")
def startup_event():
    global log_listener
    log_listener = setup_logging()
    # Start Task Manager
    from app.service.task_manager import TaskManager
    TaskManager.get_instance().start()

@app.on_event("shutdown")
def shutdown_event():
    global log_listener
    from app.service.task_manager import TaskManager
    TaskManager.get_instance().stop()

    if log_listener:
        log_listener.stop()



