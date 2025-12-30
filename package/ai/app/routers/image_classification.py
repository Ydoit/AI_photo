import logging
import traceback

from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Body
from app.services.image_classification_service import image_classification_service
from pydantic import BaseModel
from typing import List, Dict, Optional

router = APIRouter()

class ClassificationResult(BaseModel):
    label: str
    confidence: float

class ClassificationResponse(BaseModel):
    results: List[ClassificationResult]
    embedding: List[float]

class CategoryCreateRequest(BaseModel):
    key: str
    zh: str
    en: str
    prompts: List[str]

class CategoryUpdateRequest(BaseModel):
    zh: Optional[str] = None
    en: Optional[str] = None
    prompts: Optional[List[str]] = None

class TextEmbeddingRequest(BaseModel):
    text: str

@router.post("/embed/text", response_model=List[float])
async def embed_text(request: TextEmbeddingRequest):
    """
    Generate embedding for text using the loaded CLIP model.
    """
    try:
        embedding = await image_classification_service.embed_text(request.text)
        return embedding
    except Exception as e:
        logging.info(traceback.format_exc())
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/classify", response_model=ClassificationResponse)
async def classify_image(
    file: UploadFile = File(...),
    lang: str = Query("zh", pattern="^(zh|en)$", description="Language for labels (zh/en)"),
    limit: int = Query(3, ge=1, le=20, description="Number of top results to return"),
    precision: str = Query("high", pattern="^(normal|high)$", description="Classification precision mode (normal/high)")
):
    """
    Classify an uploaded image into predefined categories.
    Categories: Person, Animal, Nature, Architecture, Skiing, Sports, Others.
    
    Parameters:
    - lang: Language for labels (zh/en)
    - limit: Number of top results to return (default 3)
    - precision: 
        - normal: Faster, uses only the first prompt per category.
        - high: Slower but more accurate, uses all defined prompts per category (ensemble).
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Supported: JPG, PNG, WebP")
    
    try:
        content = await file.read()
        classification_result = await image_classification_service.classify(content, lang, limit, precision)
        
        return ClassificationResponse(
            results=[
                ClassificationResult(label=r["label"], confidence=r["confidence"])
                for r in classification_result["results"]
            ],
            embedding=classification_result["embedding"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Management Endpoints ---

@router.get("/categories", response_model=Dict)
async def get_categories():
    """
    Get all configured classification categories.
    """
    return image_classification_service.get_categories()

@router.post("/categories")
async def add_category(category: CategoryCreateRequest):
    """
    Add a new classification category.
    """
    try:
        image_classification_service.add_category(
            key=category.key,
            zh=category.zh,
            en=category.en,
            prompts=category.prompts
        )
        return {"message": f"Category '{category.key}' added successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/categories/{key}")
async def update_category(key: str, category: CategoryUpdateRequest):
    """
    Update an existing classification category.
    """
    try:
        image_classification_service.update_category(
            key=key,
            zh=category.zh,
            en=category.en,
            prompts=category.prompts
        )
        return {"message": f"Category '{key}' updated successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/categories/{key}")
async def delete_category(key: str):
    """
    Delete a classification category.
    """
    try:
        image_classification_service.delete_category(key)
        return {"message": f"Category '{key}' deleted successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
