from typing import List, Optional, Union
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models.agent import AgentSession, AgentMessage
from app.schemas.agent import AgentSessionCreate, AgentSessionUpdate, AgentMessageCreate

# ---- Session CRUD ----

def get_session(db: Session, session_id: Union[str, UUID]) -> Optional[AgentSession]:
    if isinstance(session_id, str):
        session_id = UUID(session_id)
    return db.query(AgentSession).filter(AgentSession.id == session_id).first()

def get_sessions_by_user(
    db: Session, user_id: Union[str, UUID], skip: int = 0, limit: int = 100
) -> List[AgentSession]:
    if isinstance(user_id, str):
        user_id = UUID(user_id)
    return (
        db.query(AgentSession)
        .filter(AgentSession.user_id == user_id)
        .order_by(desc(AgentSession.is_pinned), desc(AgentSession.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_session(db: Session, obj_in: AgentSessionCreate, user_id: Union[str, UUID]) -> AgentSession:
    if isinstance(user_id, str):
        user_id = UUID(user_id)
    db_obj = AgentSession(
        **obj_in.model_dump(exclude_unset=True, exclude_none=True),
        user_id=user_id,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_session(db: Session, db_obj: AgentSession, obj_in: AgentSessionUpdate) -> AgentSession:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(db_obj, field, update_data[field])
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_session(db: Session, session_id: Union[str, UUID]) -> bool:
    if isinstance(session_id, str):
        session_id = UUID(session_id)
    db_obj = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if db_obj:
        db.delete(db_obj)
        db.commit()
        return True
    return False

# ---- Message CRUD ----

def get_messages_by_session(
    db: Session, session_id: Union[str, UUID], skip: int = 0, limit: int = 100
) -> List[AgentMessage]:
    if isinstance(session_id, str):
        session_id = UUID(session_id)
    return (
        db.query(AgentMessage)
        .filter(AgentMessage.session_id == session_id)
        .order_by(AgentMessage.created_at)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_message(db: Session, obj_in: AgentMessageCreate) -> AgentMessage:
    db_obj = AgentMessage(**obj_in.model_dump())
    db.add(db_obj)
    
    # Update session's summary_update_time
    session = db.query(AgentSession).filter(AgentSession.id == obj_in.session_id).first()
    if session:
        session.summary_update_time = datetime.now()
        db.add(session)
        
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_messages_by_session(db: Session, session_id: Union[str, UUID]) -> bool:
    if isinstance(session_id, str):
        session_id = UUID(session_id)
    db.query(AgentMessage).filter(AgentMessage.session_id == session_id).delete()
    db.commit()
    return True
