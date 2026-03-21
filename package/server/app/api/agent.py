import uuid
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.db.models.user import User
from app.service.agent.service import chat_with_agent

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

@router.post("/chat", response_model=ChatResponse, summary="与智能相册助手对话")
def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    处理与 TrailSnap Agent 的对话请求。
    如果 session_id 未提供，将自动生成一个新的。
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        reply = chat_with_agent(
            user_id=str(current_user.id),
            session_id=session_id,
            user_input=request.message
        )
        return ChatResponse(response=reply, session_id=session_id)
    except ValueError as ve:
        # 捕获由于未配置 LLM 引起的异常
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")
