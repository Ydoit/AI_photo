from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.db.models.app_setting import AppSetting

from app.api import user, album, settings, index, media, stats

app = FastAPI(title="TrailSnap - 足迹相册")

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)
def _mount_uploads():
    db = SessionLocal()
    try:
        setting = db.query(AppSetting).filter(AppSetting.key == 'storage_root').first()
        root = setting.value if setting and setting.value else 'uploads'
    finally:
        db.close()
    # Still mount for backward compatibility or direct access if needed
    app.mount("/uploads", StaticFiles(directory=root), name="uploads")
_mount_uploads()

app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(album.router, prefix="/api", tags=["Albums"])
app.include_router(settings.router, prefix="/api", tags=["Settings"])
app.include_router(index.router, prefix="/api", tags=["Index"])
app.include_router(media.router, prefix="/api", tags=["Media"])
app.include_router(stats.router, prefix="/api", tags=["Stats"])

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
    _mount_uploads()


