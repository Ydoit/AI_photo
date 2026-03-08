from typing import Optional, Union, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config_manager import config_manager
from app.core.security import get_password_hash, verify_password
from app.db.models.user import User
from app.schemas.user import UserCreate

def get(db: Session, id: Union[int, str, UUID]) -> Optional[User]:
    try:
        if isinstance(id, str):
            id = UUID(id)
        return db.query(User).filter(User.id == id).first()
    except (ValueError, TypeError):
        return None

def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_by_username_or_email(db: Session, identifier: str) -> Optional[User]:
    return db.query(User).filter(
        or_(User.email == identifier, User.username == identifier)
    ).first()

def create(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    
    security_answer_hash = None
    if user.security_answer:
        security_answer_hash = get_password_hash(user.security_answer)

    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        security_question=user.security_question,
        security_answer_hash=security_answer_hash,
        settings=config_manager.get_default_config()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate(db: Session, email: str, password: str) -> Optional[User]:
    # Try by email first, then username if not found (though param says email)
    # The login form usually sends username field which might contain email
    user = get_by_username_or_email(db, email)
    
    if not user:
        return None
    
    # Check lockout
    if user.lockout_until and user.lockout_until > datetime.utcnow():
        return None # Caller should handle specific lockout message by checking user state if auth fails

    if not verify_password(password, user.hashed_password):
        # Handle failed attempt
        user.failed_login_attempts += 1
        user.last_failed_login = datetime.utcnow()
        if user.failed_login_attempts >= 5: # Threshold could be configured
             user.lockout_until = datetime.utcnow() + timedelta(minutes=15) # Lockout duration
        db.add(user)
        db.commit()
        return None
    
    # Reset failed attempts on success
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        user.lockout_until = None
        db.add(user)
        db.commit()
        
    return user

def verify_security_answer(user: User, answer: str) -> bool:
    if not user.security_answer_hash:
        return False
    return verify_password(answer, user.security_answer_hash)

def reset_password(db: Session, user: User, new_password: str):
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    # Clear lockout on password reset
    user.failed_login_attempts = 0
    user.lockout_until = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
