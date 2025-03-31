"""
User API endpointlari

User uchun API endpointlari
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import User, UserCreate, UserUpdate, UserWithFeedbacks
from app.crud import user as user_crud
from app.crud import feedback as feedback_crud
from app.core.security import get_current_active_user

router = APIRouter()



@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
        user_in: UserCreate,
        db: Session = Depends(get_db)
) -> Any:

    # Avval foydalanuvchi mavjudligini tekshirish
    db_user = user_crud.get_user_by_telegram_id(db, telegram_id=user_in.telegram_id)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram ID ro'yxatdan o'tgan"
        )

    # Foydalanuvchini yaratish
    return user_crud.create_user(db=db, user=user_in)
