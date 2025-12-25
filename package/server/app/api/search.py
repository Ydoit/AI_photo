from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
import aiohttp
from app.dependencies import get_db
from app.crud import crud_vector
from app.core.config_manager import config_manager
from app.schemas.photo import Photo
from app.crud import album as crud_album

router = APIRouter()

class SearchResult(BaseModel):
    photo: Photo
    score: float

class TextSearchRequest(BaseModel):
    text: str
    limit: int = 20
    threshold: float = 0.0

@router.post("/text", response_model=List[SearchResult])
async def search_by_text(
    request: TextSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search photos by text query using vector similarity.
    """
    try:
        # 1. Get Text Embedding from AI Service
        async with aiohttp.ClientSession() as session:
            api_url = f"{config_manager.config.ai.ai_api_url}/classification/embed/text"
            async with session.post(
                api_url,
                json={"text": request.text}
            ) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=502, detail=f"AI Service error: {resp.status}")
                embedding = await resp.json()

        # 2. Search Vectors
        results = crud_vector.search_similar_vectors(db, embedding, request.limit)

        # 3. Format Response
        response = []
        for photo_id, distance in results:
            # Convert distance to similarity score (0 to 1) if possible, 
            # or just return distance (lower is better) or 1 - distance
            # Cosine distance is 1 - cosine_similarity.
            # So score = 1 - distance.
            score = 1 - distance
            
            if score < request.threshold:
                continue

            photo = crud_album.get_photo(db, photo_id)
            if photo:
                response.append(SearchResult(photo=photo, score=score))

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/image", response_model=List[SearchResult])
async def search_by_image(
    file: UploadFile = File(...),
    limit: int = Form(20),
    threshold: float = Form(0.0),
    db: Session = Depends(get_db)
):
    """
    Search photos by image query using vector similarity.
    """
    try:
        # 1. Get Image Embedding from AI Service
        # We use /classify endpoint which returns embedding
        async with aiohttp.ClientSession() as session:
            file_content = await file.read()
            form_data = aiohttp.FormData()
            form_data.add_field('file', file_content, filename=file.filename)
            
            api_url = f"{config_manager.config.ai.ai_api_url}/classification/classify"
            async with session.post(
                api_url,
                data=form_data,
                params={"limit": 1} # We don't care about classification results
            ) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=502, detail=f"AI Service error: {resp.status}")
                result = await resp.json()
                embedding = result.get("embedding")
                if not embedding:
                    raise HTTPException(status_code=500, detail="No embedding returned from AI service")

        # 2. Search Vectors
        results = crud_vector.search_similar_vectors(db, embedding, limit)

        # 3. Format Response
        response = []
        for photo_id, distance in results:
            score = 1 - distance
            if score < threshold:
                continue
                
            photo = crud_album.get_photo(db, photo_id)
            if photo:
                response.append(SearchResult(photo=photo, score=score))

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
