"""
User API endpointlari

User uchun API endpointlari
"""
from typing import Any, List, Optional
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
    telegram_id: str,
    name: Optional[str] = None,
    is_worker: bool = False,
    db: Session = Depends(get_db),
) -> Any:
    print(user.telegram_id)
    print(user.name)
    print(user.is_worker)
    user = user_crud.get_user_by_telegram_id(db, telegram_id=telegram_id)
    if not user:
        db_user = User(
        telegram_id=telegram_id,
        name=name,
        is_worker=is_worker,
    )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

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
        
        
    