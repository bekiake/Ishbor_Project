from typing import Any, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select

from app.api.endpoints.auth import generate_access_token
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import models
from app.database import get_db as get_async_db  # Asinxron DB session
from app.schemas import schemas
from app.schemas.schemas import Token, User, UserCreate, UserOut, UserUpdate, UserWithFeedbacks, WorkerOut
from app.crud import user as user_crud
from app.crud import feedback as feedback_crud
from app.crud import worker as worker_crud
from app.core.security import get_current_active_user
import random
import string

router = APIRouter()


@router.post("/user_check")
async def check_user(
        telegram_id: str,
        db: AsyncSession = Depends(get_async_db),
) -> Any:
    # user_crud.get_user_by_telegram_id ni asinxron deb taxmin qilamiz
    user = await user_crud.get_user_by_telegram_id(db, telegram_id = telegram_id)
    if not user:
        return {"registered": False}

    # generate_access_token ni asinxron deb qoldiramiz, agar u sinxron bo'lsa keyinroq optimallashtiriladi
    token = await generate_access_token(telegram_id) if hasattr(generate_access_token,
                                                                '__call__') else generate_access_token(telegram_id)
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
        db: AsyncSession = Depends(get_async_db),
) -> Any:
    user = await user_crud.get_user_by_telegram_id(db, telegram_id = telegram_id)
    if not user:
        db_user = models.User(
            telegram_id = telegram_id,
            name = name,
            is_worker = is_worker,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        token = await generate_access_token(telegram_id) if hasattr(generate_access_token,
                                                                    '__call__') else generate_access_token(telegram_id)
        return {
            "access_token": token,
            "is_worker": is_worker,
            "name": name,
            "telegram_id": telegram_id,
            "registered": False,
        }

    else:
        worker = await worker_crud.get_worker_by_telegram_id(db, telegram_id = telegram_id)
        if not worker:
            token = await generate_access_token(telegram_id) if hasattr(generate_access_token,
                                                                        '__call__') else generate_access_token(
                telegram_id)
            return {
                "access_token": token,
                "is_worker": False,
                "name": name,
                "telegram_id": telegram_id,
                "registered": False,
            }
        else:
            token = await generate_access_token(telegram_id) if hasattr(generate_access_token,
                                                                        '__call__') else generate_access_token(
                telegram_id)
            return {
                "access_token": token,
                "is_worker": True,
                "name": name,
                "telegram_id": telegram_id,
                "registered": True,
            }


@router.get("/me", response_model=Union[UserOut, WorkerOut])
async def get_user_profile(
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    # Avvalo, foydalanuvchini bazadan olish
    user = await user_crud.get_user_by_telegram_id(
        db, telegram_id=current_user.telegram_id
    )
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Agar worker emas bo‘lsa, oddiy foydalanuvchi ma’lumotlarini qaytaramiz
    if not user.is_worker:
        return UserOut.from_orm(user)

    # Aks holda — workerni olish
    worker = await worker_crud.get_worker_by_telegram_id(
        db, telegram_id=current_user.telegram_id
    )
    if not worker:
        raise HTTPException(
            status_code=404,
            detail="Worker not found"
        )

    # Faqat topilgandan keyin image ni o‘zgartirish
    if worker.image:
        worker.image = f"https://admin.ishbozor.uz/{worker.image}"
    else:
        # image yo'q bo'lsa, None qilib qoldirish ham mumkin
        worker.image = None

    # Va tayyor worker javobi
    return WorkerOut.from_orm(worker)




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
    return ''.join(random.choices(string.digits, k = length))


def generate_random_image_url():
    """Tasodifiy image URL (placeholder) qaytaradi."""
    return "https://via.placeholder.com/150"


def generate_random_age():
    """18 dan 60 gacha tasodifiy yosh qaytaradi."""
    return random.randint(18, 60)


def generate_random_phone():
    """Tasodifiy telefon raqamini (9 raqam) hosil qiladi."""
    return ''.join(random.choices(string.digits, k = 9))


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
    selected = random.sample(possible_languages, k = random.randint(1, 3))
    return ", ".join(selected)


def generate_random_skills():
    """Tasodifiy malakalarni tanlab, vergul bilan ajratilgan string qaytaradi."""
    possible_skills = ["Python", "JavaScript", "HTML", "CSS", "FastAPI", "Django", "Docker", "SQL"]
    selected = random.sample(possible_skills, k = random.randint(1, 4))
    return ", ".join(selected)


def generate_random_location():
    """Tasodifiy joylashuvni tanlaydi."""
    possible_locations = ["Tashkent", "Samarkand", "Bukhara", "Andijan", "Namangan", "Nukus"]
    return random.choice(possible_locations)


def generate_random_disability_degree():
    """Tasodifiy nogironlik darajasini tanlaydi."""
    disability_degrees = ["1-guruh", "2-guruh", "3-guruh", "yo'q"]
    return random.choice(disability_degrees)


def generate_random_about():
    descriptions = [
        "I am a passionate developer with a love for technology and coding.",
        "An avid learner, always seeking new challenges and opportunities to grow.",
        "Creative thinker with a strong background in problem-solving and development.",
        "I enjoy working on diverse projects and collaborating with teams to bring ideas to life.",
        "Tech enthusiast with expertise in web development and a drive for continuous improvement."
    ]

    return random.choice(descriptions)


@router.post("/generate_users1")
async def generate_users(name: str, db: AsyncSession = Depends(get_async_db)) -> Any:
    created_count = 0
    try:
        for _ in range(100):
            telegram_id = generate_random_telegram_id()
            # workers_user jadvaliga foydalanuvchi qo'shish
            db_user = models.User(
                telegram_id = telegram_id,
                name = name,  # faqat bitta kiritilgan name ishlatiladi
                is_worker = True
            )
            db.add(db_user)

            if db_user.is_worker:
                worker = models.Worker(
                    telegram_id = db_user.telegram_id,
                    name = db_user.name,
                    image = generate_random_image_url(),
                    about = generate_random_about(),
                    age = generate_random_age(),
                    phone = generate_random_phone(),
                    gender = generate_random_gender(),
                    payment_type = generate_random_payment_type(),
                    daily_payment = generate_random_daily_payment(),
                    languages = generate_random_languages(),
                    skills = generate_random_skills(),
                    location = generate_random_location(),
                    disability_degree = generate_random_disability_degree(),  # Yangi maydon
                    is_active = True
                )
                db.add(worker)
                created_count += 1

        # Asinxron commit
        await db.commit()

    except Exception as e:
        await db.rollback()  # Xatolik yuz beradigan bo'lsa, rollback qilinadi
        return {"message": f"Error: {str(e)}"}

    return {
        "message": f"{created_count} worker yozuvi workers_worker jadvaliga yaratildi, name: {name}"
    }

