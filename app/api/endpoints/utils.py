"""
Utilities API endpointlari

Turli yordamchi API endpointlari
"""
from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import io
import csv
import json
import os
from pathlib import Path
import openpyxl
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
async def export_workers_excel(
        skip: int = Query(0, description="O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(1000, description="Qaytariladigan ma'lumotlar soni"),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """
    Ishchilar ro'yxatini Excel formatida eksport qilish
    """
    # Ishchilar ro'yxatini olish
    workers = await worker_crud.get_workers(db, skip=skip, limit=limit)

    # Fayl nomi va yo'li
    filename = "workers_export.xlsx"
    file_path = os.path.join(os.getcwd(), filename)

    # Excel fayl yaratish
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Ishchilar"

    # Ustun nomlari
    headers = [
        "ID", "Telegram ID", "Ism", "Haqida", "Yosh", "Telefon", "Jinsi",
        "To'lov turi", "Kunlik to'lov", "Tillar", "Ko'nikmalar",
        "Manzil", "Rasm", "Yaratilgan sana", "Yangilangan sana", "Faol"
    ]

    # Ustun nomlarini yozish
    for col_num, header in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=col_num)
        cell.value = header
        cell.font = openpyxl.styles.Font(bold=True)
        # Ustun kengligini o'rnatish
        worksheet.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = 15

    # Ma'lumotlarni yozish
    for row_num, worker in enumerate(workers, 2):
        worksheet.cell(row=row_num, column=1).value = worker.id
        worksheet.cell(row=row_num, column=2).value = worker.telegram_id
        worksheet.cell(row=row_num, column=3).value = worker.name
        worksheet.cell(row=row_num, column=4).value = worker.about
        worksheet.cell(row=row_num, column=5).value = worker.age
        worksheet.cell(row=row_num, column=6).value = worker.phone
        worksheet.cell(row=row_num, column=7).value = worker.gender
        worksheet.cell(row=row_num, column=8).value = worker.payment_type
        worksheet.cell(row=row_num, column=9).value = worker.daily_payment
        worksheet.cell(row=row_num, column=10).value = worker.languages
        worksheet.cell(row=row_num, column=11).value = worker.skills
        worksheet.cell(row=row_num, column=12).value = worker.location
        worksheet.cell(row=row_num, column=13).value = worker.image
        worksheet.cell(row=row_num, column=14).value = worker.created_at.isoformat()
        worksheet.cell(row=row_num, column=15).value = worker.updated_at.isoformat()
        worksheet.cell(row=row_num, column=16).value = "Ha" if worker.is_active else "Yo'q"

    # Faylni saqlash
    workbook.save(file_path)

    # Faylni FileResponse orqali qaytarish
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.get("/skills", response_model=List[str])
async def get_all_skills(db: AsyncSession = Depends(get_async_db)):
    return await worker_crud.get_all_skill_names(db)