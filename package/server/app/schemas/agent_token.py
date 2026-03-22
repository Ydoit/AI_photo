from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class AgentTokenBase(BaseModel):
    name: str = Field(..., description="令牌名称")

class AgentTokenCreateAPI(AgentTokenBase):
    expires_at: datetime = Field(..., description="过期时间")
    password: str = Field(..., description="用户密码，用于验证")

class AgentTokenResponse(AgentTokenBase):
    id: UUID
    user_id: UUID
    token: str
    created_at: datetime
    expires_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True
