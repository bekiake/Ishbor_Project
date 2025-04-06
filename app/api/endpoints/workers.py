"""
Worker API endpointlari

Worker uchun API endpointlari
"""
from typing import Any, List, Optional, Dict
from fastapi import (
    APIRouter, Depends, HTTPException, status, Query,
    Form, UploadFile, File, Path, Body,
)
from sqlalchemy.orm import Session
import shutil
import os
from pathlib import Path as FilePath
from ...core.security import get_current_user
from app.database import get_db
from app.schemas.schemas import (
    Worker, WorkerCreate, WorkerUpdate, WorkerWithFeedbacks,
    WorkerLocation, Feedback, WorkerSearchParams, WorkerStats
)
from app.crud import worker as worker_crud
from app.crud import feedback as feedback_crud
from app.crud import user as user_crud

from app.core.security import get_current_active_user
from app.core.settings import settings
from app.models.models import User

router = APIRouter()


@router.get("/", response_model = List[Worker])
async def read_workers(
        skip: int = Query(0, description = "O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(100, description = "Qaytariladigan ma'lumotlar soni"),
        is_active: bool = Query(True, description = "Faqat faol ishchilarni qaytarish"),
        db: Session = Depends(get_db),
) -> Any:
    
    workers = worker_crud.get_workers(db, skip = skip, limit = limit, is_active = is_active)
    return workers


@router.get("/me", response_model = dict)
async def read_worker_me(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    
    # Extract the telegram_id string from the User object
    telegram_id = current_user.telegram_id

    worker = worker_crud.get_worker_by_telegram_id(db, telegram_id)
    if not worker:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Worker not found"
        )

    # Convert worker object to dictionary with all requested fields
    worker_data = {
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
        "image": worker.image_url if hasattr(worker, "image_url") else None,
        "is_active": worker.is_active
    }

    return worker_data
@router.post("/with-image", response_model = Worker, status_code = status.HTTP_201_CREATED)
async def create_worker_with_image(
        telegram_id: str = Form(...),
        name: Optional[str] = Form(None),
        age: Optional[int] = Form(None),
        phone: Optional[str] = Form(None),
        gender: Optional[str] = Form(None),
        payment_type: Optional[str] = Form("barchasi"),
        daily_payment: Optional[int] = Form(None),
        languages: Optional[str] = Form(None),
        skills: Optional[str] = Form(None),
        location: Optional[str] = Form(None),
        image: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
   
    # Avval ishchi mavjudligini tekshirish
    db_worker = worker_crud.get_worker_by_telegram_id(db, telegram_id = telegram_id)
    if db_worker:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Telegram ID ro'yxatdan o'tgan"
        )

    # Telefon raqami unique bo'lishi kerak
    if phone:
        db_worker_by_phone = worker_crud.get_worker_by_phone(db, phone = phone)
        if db_worker_by_phone:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Telefon raqami ro'yxatdan o'tgan"
            )

    # Ishchi ma'lumotlarini yaratish
    worker_data = WorkerCreate(
        telegram_id = telegram_id,
        name = name,
        age = age,
        phone = phone,
        gender = gender,
        payment_type = payment_type,
        daily_payment = daily_payment,
        languages = languages,
        skills = skills,
        location = location,
    )

    # Ishchini yaratish
    db_worker = worker_crud.create_worker(db = db, worker = worker_data)

    # Rasmni saqlash
    if image:
        # Rasm mime turini tekshirish
        content_type = image.content_type
        if content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = f"Rasm turi qabul qilinmaydi. Qabul qilinadigan turlar: {settings.ALLOWED_IMAGE_TYPES}"
            )

        # Rasmni saqlash
        file_extension = os.path.splitext(image.filename)[1]
        filename = f"worker_{db_worker.id}{file_extension}"
        file_path = FilePath(settings.WORKER_IMAGES_DIR) / filename

        # Papkani yaratish (agar mavjud bo'lmasa)
        os.makedirs(os.path.dirname(file_path), exist_ok = True)

        # Rasmni yozish
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Rasmni worker ma'lumotlariga qo'shish
        image_url = f"{settings.MEDIA_URL}uploads/workers/{filename}"
        db_worker = worker_crud.update_worker_image(db, worker_id = db_worker.id, image_path = image_url)

    return db_worker


@router.get("/search", response_model = List[Worker])
async def search_workers(
        skills: Optional[List[str]] = Query(None, description = "Ko'nikmalar ro'yxati"),
        languages: Optional[List[str]] = Query(None, description = "Tillar ro'yxati"),
        payment_type: Optional[str] = Query(None, description = "To'lov turi"),
        gender: Optional[str] = Query(None, description = "Jinsi"),
        min_payment: Optional[int] = Query(None, description = "Minimal to'lov"),
        max_payment: Optional[int] = Query(None, description = "Maksimal to'lov"),
        location: Optional[str] = Query(None, description = "Lokatsiya (format: 'latitude,longitude')"),
        distance: Optional[float] = Query(None, description = "Masofa (km)"),
        skip: int = Query(0, description = "O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(20, description = "Qaytariladigan ma'lumotlar soni"),
        db: Session = Depends(get_db),
) -> Any:
    
    # Qidirish parametrlarini yaratish
    search_params = WorkerSearchParams(
        skills = skills,
        languages = languages,
        payment_type = payment_type,
        gender = gender,
        min_payment = min_payment,
        max_payment = max_payment,
        location = location,
        distance = distance,
    )

    # Qidirish
    workers = worker_crud.search_workers(
        db, search_params = search_params, skip = skip, limit = limit
    )

    return workers


@router.get("/{worker_id}", response_model = WorkerWithFeedbacks)
async def read_worker(
        worker_id: int = Path(..., description = "Ishchi ID si"),
        db: Session = Depends(get_db),
) -> Any:
    worker = worker_crud.get_worker(db, worker_id = worker_id)
    if worker is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Ishchi topilmadi"
        )

    
    feedbacks = feedback_crud.get_worker_feedbacks(db, worker_id = worker_id)
    if feedbacks is None:
        return worker

    else:
        worker_name = worker_crud.get_worker(db, worker_id = worker_id).name
        
        for feedback in feedbacks:
            feedback_user_name = user_crud.get_user(db, user_id = feedback.user_id).name
            
        
        worker_with_feedbacks = WorkerWithFeedbacks.from_orm(worker)
        worker_with_feedbacks.feedbacks = feedbacks
        
        
        return worker_with_feedbacks


@router.put("/{worker_id}", response_model = Worker)
async def update_worker(
        worker_id: int,
        name: Optional[str] = Form(None),
        age: Optional[int] = Form(None),
        phone: Optional[str] = Form(None),
        gender: Optional[str] = Form(None),
        payment_type: Optional[str] = Form(None),
        daily_payment: Optional[int] = Form(None),
        languages: Optional[str] = Form(None),
        skills: Optional[str] = Form(None),
        latitude: Optional[float] = Form(None),
        longitude: Optional[float] = Form(None),
        image: Optional[UploadFile] = File(None),
        is_active: Optional[bool] = Form(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Ishchi ma'lumotlarini va rasmini yangilash
    
    Berilgan ID bo'yicha ishchi ma'lumotlari va rasmini yangilaydi
    """
    worker = worker_crud.get_worker(db, worker_id = worker_id)
    if worker is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Ishchi topilmadi"
        )

    # Telefon raqami unique bo'lishi kerak
    if phone and phone != worker.phone:
        db_worker_by_phone = worker_crud.get_worker_by_phone(db, phone = phone)
        if db_worker_by_phone:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Telefon raqami ro'yxatdan o'tgan"
            )

    # Worker modeliga mos update qilish uchun ma'lumotlarni yig'ish
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if age is not None:
        update_data["age"] = age
    if phone is not None:
        update_data["phone"] = phone
    if gender is not None:
        update_data["gender"] = gender
    if payment_type is not None:
        update_data["payment_type"] = payment_type
    if daily_payment is not None:
        update_data["daily_payment"] = daily_payment
    if languages is not None:
        # Ko'p tillar vergul bilan ajratilgan bo'lishi mumkin
        worker.set_languages([lang.strip() for lang in languages.split(",")])
    if skills is not None:
        # Ko'nikmalar vergul bilan ajratilgan bo'lishi mumkin
        worker.set_skills([skill.strip() for skill in skills.split(",")])
    if latitude is not None and longitude is not None:
        worker.set_location(latitude, longitude)
    if is_active is not None:
        update_data["is_active"] = is_active

    # Ma'lumotlarni yangilash
    worker_update = WorkerUpdate(**update_data)
    worker = worker_crud.update_worker(db = db, worker_id = worker_id, worker_update = worker_update)

    # Rasm yuklangan bo'lsa, uni ham yangilash
    if image:
        # Rasm mime turini tekshirish
        content_type = image.content_type
        if content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = f"Rasm turi qabul qilinmaydi. Qabul qilinadigan turlar: {settings.ALLOWED_IMAGE_TYPES}"
            )

        # Eski rasmni o'chirish
        if worker.image:
            old_image_path = FilePath(settings.BASE_DIR) / worker.image.lstrip('/')
            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        # Yangi rasmni saqlash
        file_extension = os.path.splitext(image.filename)[1]
        filename = f"worker_{worker_id}{file_extension}"
        file_path = FilePath(settings.WORKER_IMAGES_DIR) / filename

        # Papkani yaratish (agar mavjud bo'lmasa)
        os.makedirs(os.path.dirname(file_path), exist_ok = True)

        # Rasmni yozish
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Rasmni worker ma'lumotlariga qo'shish
        image_url = f"{settings.MEDIA_URL}uploads/workers/{filename}"
        worker = worker_crud.update_worker_image(db = db, worker_id = worker_id, image_path = image_url)

    return worker


@router.patch("/{worker_id}/toggle-status", status_code = status.HTTP_200_OK)
async def toggle_worker_status(
        worker_id: int,
        is_active: bool = Body(..., embed = True),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> dict:
    worker = worker_crud.get_worker(db, worker_id = worker_id)
    if worker is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Ishchi topilmadi"
        )

    # Status o'zgartirish
    updated_worker = worker_crud.update_worker_status(
        db = db,
        worker_id = worker_id,
        is_active = is_active
    )

    if updated_worker:
        return {
            "status": "success",
            "message": f"Ishchi statusi {is_active} qiymatiga o'zgartirildi",
            "worker_id": worker_id,
            "is_active": is_active
        }
    else:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Ishchi statusini o'zgartirishda xatolik yuz berdi"
        )


@router.delete("/{worker_id}", status_code = status.HTTP_200_OK)
async def delete_worker(
        worker_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> dict:  # Dict qaytaradi
    """
    Ishchini o'chirish

    Berilgan ID bo'yicha ishchini o'chiradi
    """
    worker = worker_crud.get_worker(db, worker_id = worker_id)
    if worker is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Ishchi topilmadi"
        )

    # Ishchiga bog'langan rasmni o'chirish
    if worker.image:
        image_path = FilePath(settings.BASE_DIR) / worker.image.lstrip('/')
        if os.path.exists(image_path):
            os.remove(image_path)

    success = worker_crud.delete_worker(db = db, worker_id = worker_id)

    if success:
        return {"status": "success", "message": "Ishchi muvaffaqiyatli o'chirildi", "id": worker_id}
    else:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Ishchini o'chirishda xatolik yuz berdi"
        )
