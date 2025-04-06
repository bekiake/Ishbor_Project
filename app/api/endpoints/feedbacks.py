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


@router.post("/", response_model=Feedback, status_code=status.HTTP_201_CREATED)
async def create_feedback(
        feedback_in: FeedbackCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    user_id = current_user.id
    # Ishchi mavjudligini tekshirish
    worker = worker_crud.get_worker(db, worker_id=feedback_in.worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    # Foydalanuvchi mavjudligini tekshirish
    user = user_crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )

    # Fikr yaratish
    return feedback_crud.create_feedback(db=db, user_id=user_id,feedback=feedback_in)



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
