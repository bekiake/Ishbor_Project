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
import random
import string

router = APIRouter()

@router.post("/user_check")
async def check_user(
    telegram_id: str,
    db: Session = Depends(get_db),
) -> Any:
    user = user_crud.get_user_by_telegram_id(db, telegram_id=telegram_id)
    if not user:
        return {"registered": False}
    
    token = generate_access_token(telegram_id)
    return {
        "registered": True,
        "is_worker": user.is_worker,
        "name": user.name,
        "telegram_id": user.telegram_id,
        "access_token": token.get("access_token"),
    }

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
            "registered": False,
        }
    token = generate_access_token(user.telegram_id)
    return {
        "access_token": token,
        "name": name,
        "telegram_id": telegram_id,
        "is_worker": is_worker,
        "registered": True,
    }


# def generate_random_telegram_id(length=10):
#
#     return ''.join(random.choices(string.digits, k=length))
#
#
# @router.post("/generate_users")
# async def generate_users(db: Session = Depends(get_db)) -> Any:
#     # Create 100 users with random telegram_id and is_worker=True
#     for _ in range(100):
#         telegram_id = generate_random_telegram_id()
#         user = models.User(
#             telegram_id=telegram_id,
#             name="test",  # or generate a random name if needed
#             is_worker=True,
#         )
#         db.add(user)
#
#     db.commit()
#     return {"message": "100 users with random Telegram IDs and is_worker=True created successfully"}
#

import random
import string
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any

def generate_random_telegram_id(length=7):
    """Tasodifiy telegram_id (raqamlardan) hosil qiladi."""
    return ''.join(random.choices(string.digits, k=length))

def generate_random_image_url():
    """Tasodifiy image URL (placeholder) qaytaradi."""
    return "https://via.placeholder.com/150"

def generate_random_age():
    """18 dan 60 gacha tasodifiy yosh qaytaradi."""
    return random.randint(18, 60)

def generate_random_phone():
    """Tasodifiy telefon raqamini (9 raqam) hosil qiladi."""
    return ''.join(random.choices(string.digits, k=9))

def generate_random_gender():
    """Tasodifiy gender (male/female) tanlaydi."""
    return random.choice(["male", "female"])

def generate_random_payment_type():
    """Tasodifiy to'lov turini tanlaydi."""
    return random.choice(["barchasi", "naqd", "karta"])

def generate_random_daily_payment():
    """Tasodifiy kunlik to'lov summasini (20 dan 200 gacha) qaytaradi."""
    return random.randint(20, 200)

def generate_random_languages():
    """Tasodifiy tillarni tanlab, vergul bilan ajratilgan string qaytaradi."""
    possible_languages = ["English", "Russian", "Uzbek", "Spanish", "German"]
    selected = random.sample(possible_languages, k=random.randint(1, 3))
    return ", ".join(selected)

def generate_random_skills():
    """Tasodifiy malakalarni tanlab, vergul bilan ajratilgan string qaytaradi."""
    possible_skills = ["Python", "JavaScript", "HTML", "CSS", "FastAPI", "Django", "Docker", "SQL"]
    selected = random.sample(possible_skills, k=random.randint(1, 4))
    return ", ".join(selected)

def generate_random_location():
    """Tasodifiy joylashuvni tanlaydi."""
    possible_locations = ["Tashkent", "Samarkand", "Bukhara", "Andijan", "Namangan", "Nukus"]
    return random.choice(possible_locations)

@router.post("/generate_users1")
async def generate_users(name: str, db: Session = Depends(get_db)) -> Any:
    """
    Kiritilgan yagona name parametri orqali:
      1) 100 ta foydalanuvchi workers_user jadvalida is_worker=True bilan yaratiladi.
      2) Agar foydalanuvchi is_worker=True bo'lsa, unga mos keladigan random ma'lumotlar bilan workers_worker jadvaliga yozuv qo'shiladi.
    """
    created_count = 0
    for _ in range(100):
        telegram_id = generate_random_telegram_id()
        # workers_user jadvaliga foydalanuvchi qo'shish
        db_user = models.User(
            telegram_id=telegram_id,
            name=name,  # faqat bitta kiritilgan name ishlatiladi
            is_worker=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Agar foydalanuvchi is_worker=True bo'lsa, workers_worker jadvaliga ma'lumot kiritish
        if db_user.is_worker:
            worker = models.Worker(
                telegram_id=db_user.telegram_id,
                name=db_user.name,
                image=generate_random_image_url(),
                age=generate_random_age(),
                phone=generate_random_phone(),
                gender=generate_random_gender(),
                payment_type=generate_random_payment_type(),
                daily_payment=generate_random_daily_payment(),
                languages=generate_random_languages(),
                skills=generate_random_skills(),
                location=generate_random_location(),
                is_active=True
            )
            db.add(worker)
            created_count += 1

    db.commit()

    return {
        "message": f"{created_count} worker yozuvi workers_worker jadvaliga yaratildi, name: {name}"
    }
