from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.db.models.app_setting import AppSetting

from app.api import user, album, settings, index, media, stats, photo, tasks

app = FastAPI(title="TrailSnap - 足迹相册")


app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(photo.router, prefix="/photos", tags=["Photos"])
app.include_router(album.router,prefix="/albums", tags=["Albums"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
app.include_router(index.router, prefix="/index", tags=["Index"])
app.include_router(media.router, prefix="/media", tags=["Media"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])

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
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE albums ADD COLUMN IF NOT EXISTS cover UUID"))
        conn.execute(text("ALTER TABLE albums ADD COLUMN IF NOT EXISTS type VARCHAR(20) DEFAULT 'user'"))
        conn.execute(text("ALTER TABLE albums ADD COLUMN IF NOT EXISTS num_photos INTEGER DEFAULT 0"))
    
    # Start Task Manager
    from app.service.task_manager import TaskManager
    TaskManager.get_instance().start()

@app.on_event("shutdown")
def shutdown_event():
    from app.service.task_manager import TaskManager
    TaskManager.get_instance().stop()



