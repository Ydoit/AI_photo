#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time        : 2025/10/14 20:38 
@Author      : SiYuan 
@Email       : sixyuan044@gmail.com
@File        : TrailSnapAPI-main.py 
@Description : 
"""
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
import os
from dotenv import load_dotenv
from starlette.staticfiles import StaticFiles

if not os.path.exists('./data'):
    os.mkdir('./data')
load_dotenv('./data/.env')

from app.api import user, train_ticket, album
from railway.api import router as railway_router

app = FastAPI(title="TrailSnap - 足迹相册")
# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
# 配置允许跨域的源（生产环境建议指定具体域名，不要用 "*"）
origins = [
    "http://localhost:8080",  # Vue开发环境地址
    "http://localhost:5173",  # Vite开发环境地址
    "http://localhost:5176",  # Vite开发环境地址
    "https://your-production-domain.com"  # 生产环境前端域名
]

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的源
    allow_credentials=True,  # 允许携带Cookie
    allow_methods=["*"],     # 允许所有HTTP方法
    allow_headers=["*"],     # 允许所有请求头
)

# 示例接口
@app.get("/")
def root():
    return {"message": "Image Manager Backend Ready"}

app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(train_ticket.router, prefix="/api/train-ticket", tags=["train-ticket"])
app.include_router(railway_router, prefix="/api/railway", tags=["railway"])
app.include_router(album.router, prefix="/api", tags=["Albums"])

if __name__ == "__main__":
    import uvicorn
    # http://127.0.0.1:8000/docs
    uvicorn.run(app, host="0.0.0.0", port=8000)
