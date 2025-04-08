"""
Utilities API endpointlari

Turli yordamchi API endpointlari
"""
from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import io
import csv
import json
import os
from pathlib import Path

from app.database import get_db as get_async_db 
from app.core.security import get_current_active_user
from app.core.settings import settings
from app.models.models import User
from app.crud import worker as worker_crud
from app.crud import feedback as feedback_crud
from app.crud import user as user_crud

router = APIRouter()




@router.get("/stats/system")
async def get_system_stats(
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    
    # Foydalanuvchilar soni
    users_count = await user_crud.get_user_count(db)
    active_users_count = await user_crud.get_active_user_count(db)

    # Ishchilar statistikasi
    worker_stats = await worker_crud.get_worker_statistics(db)

    # Fikrlar statistikasi
    feedback_stats = await feedback_crud.get_feedback_statistics(db)

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
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Ishchilar ro'yxatini CSV formatida eksport qilish
    """
    # Ishchilar ro'yxatini olish
    workers = await worker_crud.get_workers(db, skip=skip, limit=limit)

    # CSV fayl yaratish
    csv_content = io.StringIO()
    fieldnames = [
        "id", "telegram_id", "name", "about","age", "phone", "gender",
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
            "about": worker.about,
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

@router.get("/skills", response_model=List[str])
async def get_all_skills(db: AsyncSession = Depends(get_async_db)):
    return await worker_crud.get_all_skill_names(db)