import traceback
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core.config_manager import config_manager
from app.crud import user as crud_user
from app.db.models.user import User
from app.schemas.token import TokenPayload
from app.dependencies import get_db

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_user(
        db: Session = Depends(get_db),
        token: str = Depends(reusable_oauth2)
) -> User:
    print(token)
    try:
        payload = jwt.decode(
            token, config_manager.config.security.secret_key, algorithms=[config_manager.config.security.algorithm]
        )
        print(payload)
        token_data = TokenPayload(**payload)
    except ExpiredSignatureError:  # 专门捕获令牌过期异常
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,  # 401 未授权
            detail="Token has expired",  # 明确提示令牌过期
            headers={"WWW-Authenticate": "Bearer"},  # 符合OAuth2规范
        )
    except (JWTError, ValidationError):  # 捕获其他JWT验证错误
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,  # 403 禁止访问（其他验证错误）
            detail="Could not validate credentials",
        )

    user = crud_user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
