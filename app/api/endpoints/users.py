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


@router.get("/", response_model=List[User])
async def read_users(
        skip: int = Query(0, description="O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(100, description="Qaytariladigan ma'lumotlar soni"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Foydalanuvchilar ro'yxatini olish

    Har bir foydalanuvchi haqida asosiy ma'lumotlarni qaytaradi
    """
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users


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


@router.get("/me", response_model=User)
async def read_user_me(
        current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Joriy foydalanuvchi ma'lumotlarini olish

    Token orqali autentifikatsiya qilingan foydalanuvchi ma'lumotlarini qaytaradi
    """
    return current_user


@router.put("/me", response_model=User)
async def update_user_me(
        user_in: UserUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Joriy foydalanuvchi ma'lumotlarini yangilash
    """
    return user_crud.update_user(db=db, user_id=current_user.id, user_update=user_in)


@router.get("/me/feedbacks", response_model=List[UserWithFeedbacks])
async def read_user_feedbacks(
        skip: int = Query(0, description="O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(10, description="Qaytariladigan ma'lumotlar soni"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Joriy foydalanuvchi tomonidan qoldirilgan fikrlar ro'yxatini olish
    """
    feedbacks = feedback_crud.get_user_feedbacks(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )

    user_with_feedbacks = UserWithFeedbacks.from_orm(current_user)
    user_with_feedbacks.feedbacks = feedbacks

    return user_with_feedbacks


@router.get("/{user_id}", response_model=User)
async def read_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Foydalanuvchi ma'lumotlarini olish

    Berilgan ID bo'yicha foydalanuvchi ma'lumotlarini qaytaradi
    """
    user = user_crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )
    return user


@router.put("/{user_id}", response_model=User)
async def update_user(
        user_id: int,
        user_in: UserUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Foydalanuvchi ma'lumotlarini yangilash

    Berilgan ID bo'yicha foydalanuvchi ma'lumotlarini yangilaydi
    """
    user = user_crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )

    # TODO: Permission tekshirish kerak (admin yoki o'zi)

    user = user_crud.update_user(db=db, user_id=user_id, user_update=user_in)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> dict:
    user = user_crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )

    # Permission tekshirish kerak (admin yoki o'zi)

    success = user_crud.delete_user(db=db, user_id=user_id)

    if success:
        return {"status": "success", "message": "Foydalanuvchi muvaffaqiyatli o'chirildi", "id": user_id}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Foydalanuvchini o'chirishda xatolik yuz berdi"
        )


@router.get("/check-feedback", response_model=bool)
async def check_user_feedback(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Foydalanuvchi berilgan ishchi haqida fikr qoldirganini tekshirish"""
    feedback = feedback_crud.check_user_feedback_for_worker(
        db, worker_id=worker_id, user_id=current_user.id
    )
    return feedback is not None