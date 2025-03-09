"""
Utilities API endpointlari

Turli yordamchi API endpointlari
"""
from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
import io
import csv
import json
import os
from pathlib import Path

from app.database import get_db
from app.core.security import get_current_active_user
from app.core.settings import settings
from app.models.models import User
from app.crud import worker as worker_crud
from app.crud import feedback as feedback_crud
from app.crud import user as user_crud

router = APIRouter()


@router.get("/health")
async def health_check() -> Any:
    """
    Health check

    Aplikatsiya holati va sozlamalarini tekshirish
    """
    return {
        "status": "healthy",
        "environment": "production" if not settings.DEBUG else "development",
        "database": settings.SQLALCHEMY_DATABASE_URL.split("://")[0],
        "allowed_hosts": settings.ALLOWED_HOSTS,
        "debug": settings.DEBUG,
    }


@router.get("/stats/system")
async def get_system_stats(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Tizim statistikasi

    Tizim bo'yicha umumiy statistika ma'lumotlarini olish
    """
    # Foydalanuvchilar soni
    users_count = user_crud.get_user_count(db)
    active_users_count = user_crud.get_active_user_count(db)

    # Ishchilar statistikasi
    worker_stats = worker_crud.get_worker_statistics(db)

    # Fikrlar statistikasi
    feedback_stats = feedback_crud.get_feedback_statistics(db)

    # Ko'nikmalar va tillar
    top_skills = []
    top_languages = []

    return {
        "total_users": users_count,
        "active_users": active_users_count,
        "total_workers": worker_stats["total_workers"],
        "active_workers": worker_stats["active_workers"],
        "total_feedbacks": feedback_stats["total_feedbacks"],
        "active_feedbacks": feedback_stats["active_feedbacks"],
        "average_rating": feedback_stats["average_rating"],
        "rating_distribution": feedback_stats["rating_distribution"],
        "payment_distribution": worker_stats["payment_distribution"],
        "gender_distribution": worker_stats["gender_distribution"],
        "top_skills": top_skills,
        "top_languages": top_languages,
    }


@router.post("/export/workers")
async def export_workers_csv(
        skip: int = Query(0, description="O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(1000, description="Qaytariladigan ma'lumotlar soni"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Ishchilar ro'yxatini CSV formatida eksport qilish
    """
    # Ishchilar ro'yxatini olish
    workers = worker_crud.get_workers(db, skip=skip, limit=limit)

    # CSV fayl yaratish
    csv_content = io.StringIO()
    fieldnames = [
        "id", "telegram_id", "name", "age", "phone", "gender",
        "payment_type", "daily_payment", "languages", "skills",
        "location", "image", "created_at", "updated_at", "is_active"
    ]

    writer = csv.DictWriter(csv_content, fieldnames=fieldnames)
    writer.writeheader()

    for worker in workers:
        writer.writerow({
            "id": worker.id,
            "telegram_id": worker.telegram_id,
            "name": worker.name,
            "age": worker.age,
            "phone": worker.phone,
            "gender": worker.gender,
            "payment_type": worker.payment_type,
            "daily_payment": worker.daily_payment,
            "languages": worker.languages,
            "skills": worker.skills,
            "location": worker.location,
            "image": worker.image,
            "created_at": worker.created_at.isoformat(),
            "updated_at": worker.updated_at.isoformat(),
            "is_active": worker.is_active,
        })

    return {
        "filename": "workers_export.csv",
        "content": csv_content.getvalue(),
        "media_type": "text/csv",
    }


@router.post("/files/upload")
async def upload_file(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Fayl yuklash

    Fayl yuklash uchun endpoint
    """
    # Fayl nomini olish
    file_name = file.filename
    file_extension = os.path.splitext(file_name)[1].lower()

    # Fayl turini tekshirish
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".xlsx", ".xls", ".csv"]
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fayl turi qabul qilinmaydi. Qabul qilinadigan turlar: {', '.join(allowed_extensions)}"
        )

    # Fayl hajmini tekshirish
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fayl hajmi juda katta. Maksimal hajm: {settings.MAX_UPLOAD_SIZE / (1024 * 1024)}MB"
        )

    # Faylni saqlash
    file_path = Path(settings.UPLOAD_DIR) / f"{current_user.id}_{file_name}"

    # Papkani yaratish (agar mavjud bo'lmasa)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Faylni yozish
    with open(file_path, "wb") as f:
        f.write(contents)

    # Fayl URL sini qaytarish
    file_url = f"{settings.MEDIA_URL}uploads/{current_user.id}_{file_name}"

    return {
        "filename": file_name,
        "content_type": file.content_type,
        "size": len(contents),
        "url": file_url,
    }