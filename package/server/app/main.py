from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api import user, album

app = FastAPI(title="TrailSnap - 足迹相册")

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(album.router, prefix="/api", tags=["Albums"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Image Manager Backend Ready"}




