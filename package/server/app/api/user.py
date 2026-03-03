from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.crud.user import create
from app.dependencies import get_db
from app.api import deps
from app.db.models.user import User
from app.db.models.photo import Photo
from app.db.models.album import Album

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve users.
    """
    if not current_user.is_superuser:
        return [current_user]
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=UserResponse)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create new user.
    """
    # TODO: Check if user exists (email/username)
    return create(db, user)

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a user.
    """
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete associated data (Albums, Photos) - Only DB records
    db.query(Photo).filter(Photo.owner_id == user_id).delete()
    db.query(Album).filter(Album.owner_id == user_id).delete()

    db.delete(user)
    db.commit()
    return user
