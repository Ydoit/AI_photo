import uvicorn
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import system, face, ocr, object_detection, tickets
from app.core.logger import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    global log_listener
    log_listener = setup_logging()
    yield
    if log_listener:
        log_listener.stop()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Microservice for AI capabilities including Face Recognition, OCR, etc.",
    lifespan=lifespan
)

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


# Include Routers
app.include_router(system.router, tags=["System"])
app.include_router(face.router, tags=["Face Recognition"])
app.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
app.include_router(object_detection.router, prefix="/object-detection", tags=["Object Detection"])
app.include_router(tickets.router, prefix="/tickets", tags=["Ticket Recognition"])

if __name__ == "__main__":
    # docs：http://localhost:8001/docs
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
