"""
Authentication API endpointlari

JWT token authentication uchun API endpointlari
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import Token, User, UserCreate
from app.crud import user as user_crud
from app.core.security import create_access_token

router = APIRouter()

# Faqat Bearer token orqali kirish uchun
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")


@router.post("/token", response_model=Token)
async def login_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db),
) -> Any:
    """
    OAuth2 compatible token login

    Form data orqali login qilish va JWT token olish
    """
    telegram_id = form_data.username

    user = user_crud.get_user_by_telegram_id(db, telegram_id=telegram_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram ID noto'g'ri",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=telegram_id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=Token)
async def register_user(
        user_in: UserCreate,
        db: Session = Depends(get_db),
) -> Any:
    """
    Yangi foydalanuvchi ro'yxatdan o'tkazish va token olish

    - **telegram_id**: Foydalanuvchining Telegram ID si (majburiy)
    - **name**: Foydalanuvchi ismi (ixtiyoriy)
    """
    db_user = user_crud.get_user_by_telegram_id(db, telegram_id=user_in.telegram_id)
    if db_user:
        access_token = create_access_token(subject=db_user.telegram_id)
        return {"access_token": access_token, "token_type": "bearer"}

    user = user_crud.create_user(db=db, user=user_in)
    access_token = create_access_token(subject=user.telegram_id)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/telegram-auth", response_model=Token)
async def telegram_auth(
        telegram_id: str,
        name: str = None,
        db: Session = Depends(get_db),
) -> Any:
    """
    Telegram orqali autentifikatsiya

    - **telegram_id**: Foydalanuvchining Telegram ID si (majburiy)
    - **name**: Foydalanuvchi ismi (ixtiyoriy)
    """
    db_user = user_crud.get_user_by_telegram_id(db, telegram_id=telegram_id)

    if db_user:
        if name and name != db_user.name:
            db_user = user_crud.update_user_by_telegram_id(
                db=db,
                telegram_id=telegram_id,
                user_update=UserCreate(telegram_id=telegram_id, name=name),
            )
    else:
        db_user = user_crud.create_user(
            db=db,
            user=UserCreate(telegram_id=telegram_id, name=name),
        )

    access_token = create_access_token(subject=db_user.telegram_id)

    return {"access_token": access_token, "token_type": "bearer"}
