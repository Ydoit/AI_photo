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
from starlette.middleware.gzip import GZipMiddleware, GZipResponder
from fastapi import FastAPI, HTTPException, Request
import os
import logging
import time
from dotenv import load_dotenv
from starlette.staticfiles import StaticFiles
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

if not os.path.exists('./data'):
    os.mkdir('./data')
load_dotenv('./data/.env')

from app.api import user, train_ticket, album, index, settings, face
from railway.api import router as railway_router
from app.db.session import engine, SessionLocal
from app.api import user, album, settings, index, media, stats, photo, tasks
from app.core.logger import setup_logging

app = FastAPI(title="TrailSnap - 足迹相册")

from app.service.task_manager import TaskManager

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
# 自定义 GZip 中间件
class CustomGZipMiddleware(GZipMiddleware):
    def __init__(
        self, app, minimum_size: int = 500, compresslevel: int = 9, exclude_paths=None
    ) -> None:
        super().__init__(app, minimum_size, compresslevel)
        self.exclude_paths = exclude_paths or []

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = Headers(scope=scope)
            request = Request(scope, receive)
            if "gzip" in headers.get("Accept-Encoding", "") and not any(request.url.path.endswith(suffix) for suffix in self.exclude_paths):
                responder = GZipResponder(
                    self.app, self.minimum_size, compresslevel=self.compresslevel
                )
                await responder(scope, receive, send)
                return
        await self.app(scope, receive, send)

# 添加 GZip 中间件
exclude_paths = ['/ai_communication/AiCommunicationThemesRecord/chat']
app.add_middleware(CustomGZipMiddleware, minimum_size=1000, compresslevel=9, exclude_paths=exclude_paths)

@app.on_event("startup")
async def startup_event():
    global log_listener
    log_listener = setup_logging()
    # Start Task Manager
    TaskManager.get_instance().start()

@app.on_event("shutdown")
async def shutdown_event():
    global log_listener
    TaskManager.get_instance().stop()
    if log_listener:
        log_listener.stop()

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
app.include_router(train_ticket.router, prefix="/train-ticket", tags=["train-ticket"])
app.include_router(railway_router, prefix="/railway", tags=["railway"])
app.include_router(photo.router, prefix="/photos", tags=["Photos"])
app.include_router(album.router,prefix="/albums", tags=["Albums"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
app.include_router(index.router, prefix="/index", tags=["Index"])
app.include_router(media.router, prefix="/medias", tags=["Media"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(face.router, prefix="/faces", tags=["Faces"])

if __name__ == "__main__":
    import uvicorn
    # http://127.0.0.1:8000/docs
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=60)
