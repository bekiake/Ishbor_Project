"""
Feedback API endpointlari

Feedback uchun API endpointlari
"""
import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import Feedback, FeedbackCreate, FeedbackUpdate, Feedbackss
from app.crud import feedback as feedback_crud
from app.crud import worker as worker_crud
from app.crud import user as user_crud
from app.core.security import get_current_active_user
from app.models.models import User

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_feedback(
    worker_id: int,
    text: str = Query(..., min_length=1, max_length=500),  # Fikr matni 1 dan 500 ta belgigacha bo'lishi kerak
    rate: int = Query(..., ge=1, le=5),  # Rate 1 dan 5 gacha bo'lishi kerak
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    user_id = current_user.id  # Hozirgi autentifikatsiyalangan foydalanuvchining ID sini olish

    # Worker mavjudligini tekshirish
    worker = worker_crud.get_worker(db, worker_id=worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    # Feedback yaratish
    db_feedback = Feedbackss(
        worker_id=worker_id,
        user_id=user_id,  # Foydalanuvchi ID sini qo'shish
        rate=rate,
        text=text,
        create_at=datetime.datetime.utcnow(),  # Yaratilish sanasini o'rnatish
        update_at=datetime.datetime.utcnow(),  # Yangilanish sanasini o'rnatish
        user_name=current_user.name,  # Agar kerak bo'lsa, foydalanuvchi nomini qo'shish
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)  # Yaratilgan feedbackni yangilash
    return {
        "status": "success",
        "worker_id": worker_id,
        "user_id": user_id,
        "user_name": current_user.name,
        "rate": rate,
        "text": text
    }




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
