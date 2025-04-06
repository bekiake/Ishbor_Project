"""
User API endpointlari

User uchun API endpointlari
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.endpoints.auth import generate_access_token
from sqlalchemy.orm import Session
from app.models import models
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
    user = user_crud.get_user_by_telegram_id(db, telegram_id=telegram_id)
    if not user:
        db_user = models.User(
        telegram_id=telegram_id,
        name=name,
        is_worker=is_worker,
        
    )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        token = generate_access_token(telegram_id)
        return {
            "access_token": token,
            "is_worker": is_worker,
            "name": name,
            "telegram_id": telegram_id,
            "registered": True,
        }
    token = generate_access_token(user.telegram_id)
    return {
        "access_token": token,
        "name": name,
        "telegram_id": telegram_id,
        "is_worker": is_worker,
        "registered": False,
    }


def generate_random_telegram_id(length=10):
    """Generate a random Telegram ID (string of digits)."""
    return ''.join(random.choices(string.digits, k=length))


@router.post("/generate_users")
async def generate_users(db: Session = Depends(get_db)) -> Any:
    # Create 100 users with random telegram_id and is_worker=True
    for _ in range(100):
        telegram_id = generate_random_telegram_id()
        user = models.User(
            telegram_id=telegram_id,
            name="test",  # or generate a random name if needed
            is_worker=True,
        )
        db.add(user)

    db.commit()
    return {"message": "100 users with random Telegram IDs and is_worker=True created successfully"}