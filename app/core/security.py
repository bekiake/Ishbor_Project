"""
Authentication va security

JWT token yaratish va tekshirish uchun funksiyalar
"""
from datetime import datetime, timedelta
from typing import Any, Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.database import get_db
from app.crud import user as user_crud

from fastapi.security import OAuth2PasswordBearer

# OAuth2 sxema - endpoint token URL
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",  # "/auth/token" emas, aynan token URL bo‘lishi kerak!
    scheme_name="Bearer",
    description="HTTP Authorization header with JWT token, prefixed by 'Bearer'"
)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # JWT payload
    to_encode = {"exp": expire, "sub": str(subject)}

    # Token yaratish
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    
    try:
        # Tokenni dekodlash
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        telegram_id: str = payload.get("sub")

        # Muddati o'tganligini tekshirish
        expire = payload.get("exp")
        if expire is None or datetime.utcnow() > datetime.fromtimestamp(expire):
            return None

        return telegram_id
    except JWTError:
        return None


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Tokenni tekshirish
    telegram_id = verify_token(token)
    if telegram_id is None:
        raise credentials_exception

    # Foydalanuvchini topish
    user = user_crud.get_user_by_telegram_id(db, telegram_id=telegram_id)
    if user is None:
        raise credentials_exception

    # Foydalanuvchi faol emasligini tekshirish
    return user


async def get_current_active_user(current_user=Depends(get_current_user)):

    return current_user