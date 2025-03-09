"""
Feedback API endpointlari

Feedback uchun API endpointlari
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import Feedback, FeedbackCreate, FeedbackUpdate
from app.crud import feedback as feedback_crud
from app.crud import worker as worker_crud
from app.crud import user as user_crud
from app.core.security import get_current_active_user
from app.models.models import User

router = APIRouter()


@router.get("/", response_model=List[Feedback])
async def read_feedbacks(
        skip: int = Query(0, description="O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(100, description="Qaytariladigan ma'lumotlar soni"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Fikrlar ro'yxatini olish

    Eng so'nggi fikrlar ro'yxatini qaytaradi
    """
    feedbacks = feedback_crud.get_recent_feedbacks(db, skip=skip, limit=limit)
    return feedbacks


@router.post("/", response_model=Feedback, status_code=status.HTTP_201_CREATED)
async def create_feedback(
        feedback_in: FeedbackCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Yangi fikr yaratish

    - **worker_id**: Ishchi ID si
    - **user_id**: Foydalanuvchi ID si
    - **rate**: Reyting (1 dan 5 gacha)
    - **text**: Fikr matni (ixtiyoriy)
    """
    # Ishchi mavjudligini tekshirish
    worker = worker_crud.get_worker(db, worker_id=feedback_in.worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    # Foydalanuvchi mavjudligini tekshirish
    user = user_crud.get_user(db, user_id=feedback_in.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )

    # Fikr yaratish
    return feedback_crud.create_feedback(db=db, feedback=feedback_in)


@router.get("/worker/{worker_id}", response_model=List[Feedback])
async def read_worker_feedbacks(
        worker_id: int = Path(..., description="Ishchi ID si"),
        skip: int = Query(0, description="O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(10, description="Qaytariladigan ma'lumotlar soni"),
        db: Session = Depends(get_db),
) -> Any:
    """
    Ishchi haqidagi fikrlar ro'yxatini olish

    Berilgan ishchi ID si bo'yicha fikrlar ro'yxatini qaytaradi
    """
    # Ishchi mavjudligini tekshirish
    worker = worker_crud.get_worker(db, worker_id=worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    # Fikrlarni olish
    feedbacks = feedback_crud.get_worker_feedbacks(
        db, worker_id=worker_id, skip=skip, limit=limit
    )

    return feedbacks


@router.get("/worker/{worker_id}/rating")
async def read_worker_rating(
        worker_id: int = Path(..., description="Ishchi ID si"),
        db: Session = Depends(get_db),
) -> Any:
    """
    Ishchining o'rtacha reytingini olish

    Berilgan ishchi ID si bo'yicha o'rtacha reytingni qaytaradi
    """
    # Ishchi mavjudligini tekshirish
    worker = worker_crud.get_worker(db, worker_id=worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    # O'rtacha reytingni olish
    avg_rating = feedback_crud.get_worker_average_rating(db, worker_id=worker_id)

    return {"worker_id": worker_id, "average_rating": avg_rating}


@router.get("/user/{user_id}", response_model=List[Feedback])
async def read_user_feedbacks(
        user_id: int = Path(..., description="Foydalanuvchi ID si"),
        skip: int = Query(0, description="O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(10, description="Qaytariladigan ma'lumotlar soni"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Foydalanuvchi tomonidan qoldirilgan fikrlar ro'yxatini olish

    Berilgan foydalanuvchi ID si bo'yicha fikrlar ro'yxatini qaytaradi
    """
    # Foydalanuvchi mavjudligini tekshirish
    user = user_crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )

    # Fikrlarni olish
    feedbacks = feedback_crud.get_user_feedbacks(
        db, user_id=user_id, skip=skip, limit=limit
    )

    return feedbacks


@router.get("/{feedback_id}", response_model=Feedback)
async def read_feedback(
        feedback_id: int = Path(..., description="Fikr ID si"),
        db: Session = Depends(get_db),
) -> Any:
    """
    Fikr ma'lumotlarini olish

    Berilgan ID bo'yicha fikr ma'lumotlarini qaytaradi
    """
    feedback = feedback_crud.get_feedback(db, feedback_id=feedback_id)
    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fikr topilmadi"
        )

    return feedback


@router.put("/{feedback_id}", response_model=Feedback)
async def update_feedback(
        feedback_id: int,
        feedback_in: FeedbackUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Fikr ma'lumotlarini yangilash

    Berilgan ID bo'yicha fikr ma'lumotlarini yangilaydi
    """
    feedback = feedback_crud.get_feedback(db, feedback_id=feedback_id)
    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fikr topilmadi"
        )

    # Foydalanuvchi o'zining fikrini o'zgartirishi kerak
    if feedback.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu fikrni o'zgartirish huquqingiz yo'q"
        )

    return feedback_crud.update_feedback(
        db=db, feedback_id=feedback_id, feedback_update=feedback_in
    )


@router.delete("/{feedback_id}", status_code=status.HTTP_200_OK)
async def delete_feedback(
        feedback_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> dict:
    feedback = feedback_crud.get_feedback(db, feedback_id=feedback_id)
    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fikr topilmadi"
        )

    # Foydalanuvchi o'zining fikrini o'chirishi kerak
    if feedback.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu fikrni o'chirish huquqingiz yo'q"
        )

    success = feedback_crud.delete_feedback(db=db, feedback_id=feedback_id)

    if success:
        return {"status": "success", "message": "Fikr muvaffaqiyatli o'chirildi", "id": feedback_id}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fikrni o'chirishda xatolik yuz berdi"
        )
