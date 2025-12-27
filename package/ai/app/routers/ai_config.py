from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.ai_config_manager import ai_config_manager
from app.services.model_downloader import model_downloader
from app.services.model_manager import model_manager
import logging

router = APIRouter()

class ModelSelectionRequest(BaseModel):
    task: str
    model: str

@router.get("/config", response_model=Dict[str, Any])
async def get_config():
    """Get the current AI configuration."""
    return ai_config_manager.get_config()

@router.post("/config/model", response_model=Dict[str, Any])
async def set_model(request: ModelSelectionRequest, background_tasks: BackgroundTasks):
    """
    Set the model for a specific task.
    Triggers model download if necessary.
    """
    try:
        changed = ai_config_manager.set_model_selection(request.task, request.model)
        
        if changed:
            logging.info(f"Model selection changed for {request.task} to {request.model}")
            # Mapping from task name to manager key
            manager_key_map = {
                "ocr": "ocr",
                "face": "face",
                "classification": ["clip_text", "clip_image"]
            }
            
            keys = manager_key_map.get(request.task)
            
            # Release old models
            if keys:
                if isinstance(keys, list):
                    for k in keys:
                         try:
                             if k in model_manager.models:
                                 model_manager.models[k].release()
                         except Exception as e:
                             logging.warning(f"Failed to release model {k}: {e}")
                else:
                    try:
                         if keys in model_manager.models:
                             model_manager.models[keys].release()
                    except Exception as e:
                         logging.warning(f"Failed to release model {keys}: {e}")

            # Trigger download/check for new models
            if keys:
                 if isinstance(keys, list):
                     for k in keys:
                         model_downloader.reset_status(k)
                         model_downloader.trigger_download(k)
                 else:
                     model_downloader.reset_status(keys)
                     model_downloader.trigger_download(keys)

        return {"status": "success", "config": ai_config_manager.get_config()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Failed to set model: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
