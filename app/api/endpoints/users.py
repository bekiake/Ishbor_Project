"""
User API endpointlari

User uchun API endpointlari
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.endpoints.auth import generate_access_token
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import Token, User, UserCreate, UserUpdate, UserWithFeedbacks
from app.crud import user as user_crud
from app.crud import feedback as feedback_crud
from app.core.security import get_current_active_user

router = APIRouter()



@router.post("/register")
async def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> Any:
    
    user = user_crud.get_user_by_telegram_id(db, telegram_id=user_in.telegram_id)
    if not user:
        user = user_crud.create_user(db=db, user=user_in)
        token = generate_access_token(user.telegram_id)
        return {
            "access_token": token,
            "user": user,
            "registered": True,
        }
    token = generate_access_token(user.telegram_id)
    return {
        "access_token": token,
        "user": user,
        "registered": False,
    }
        
        
    