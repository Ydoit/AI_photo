from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import user

app = FastAPI(title="TrailSnap - 足迹相册")

app.include_router(user.router, prefix="/users", tags=["Users"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Image Manager Backend Ready"}




