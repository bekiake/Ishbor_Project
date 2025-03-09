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

from app.database import get_db
from app.schemas.schemas import (
    Worker, WorkerCreate, WorkerUpdate, WorkerWithFeedbacks,
    WorkerLocation, Feedback, WorkerSearchParams, WorkerStats
)
from app.crud import worker as worker_crud
from app.crud import feedback as feedback_crud
from app.core.security import get_current_active_user
from app.core.settings import settings
from app.models.models import User

router = APIRouter()


@router.get("/", response_model=List[Worker])
async def read_workers(
        skip: int = Query(0, description="O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(100, description="Qaytariladigan ma'lumotlar soni"),
        is_active: bool = Query(True, description="Faqat faol ishchilarni qaytarish"),
        db: Session = Depends(get_db),
) -> Any:
    """
    Ishchilar ro'yxatini olish

    Har bir ishchi haqida asosiy ma'lumotlarni qaytaradi
    """
    workers = worker_crud.get_workers(db, skip=skip, limit=limit, is_active=is_active)
    return workers


@router.post("/", response_model=Worker, status_code=status.HTTP_201_CREATED)
async def create_worker(
        worker_in: WorkerCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    # Avval ishchi mavjudligini tekshirish
    db_worker = worker_crud.get_worker_by_telegram_id(db, telegram_id=worker_in.telegram_id)
    if db_worker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram ID ro'yxatdan o'tgan"
        )

    # Telefon raqami unique bo'lishi kerak
    if worker_in.phone:
        db_worker_by_phone = worker_crud.get_worker_by_phone(db, phone=worker_in.phone)
        if db_worker_by_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telefon raqami ro'yxatdan o'tgan"
            )

    # Ishchini yaratish
    return worker_crud.create_worker(db=db, worker=worker_in)


@router.post("/with-image", response_model=Worker, status_code=status.HTTP_201_CREATED)
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
    """
    Yangi ishchi yaratish (rasm bilan)

    Form data orqali ma'lumotlarni va rasmni yuborish mumkin
    """
    # Avval ishchi mavjudligini tekshirish
    db_worker = worker_crud.get_worker_by_telegram_id(db, telegram_id=telegram_id)
    if db_worker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram ID ro'yxatdan o'tgan"
        )

    # Telefon raqami unique bo'lishi kerak
    if phone:
        db_worker_by_phone = worker_crud.get_worker_by_phone(db, phone=phone)
        if db_worker_by_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telefon raqami ro'yxatdan o'tgan"
            )

    # Ishchi ma'lumotlarini yaratish
    worker_data = WorkerCreate(
        telegram_id=telegram_id,
        name=name,
        age=age,
        phone=phone,
        gender=gender,
        payment_type=payment_type,
        daily_payment=daily_payment,
        languages=languages,
        skills=skills,
        location=location,
    )

    # Ishchini yaratish
    db_worker = worker_crud.create_worker(db=db, worker=worker_data)

    # Rasmni saqlash
    if image:
        # Rasm mime turini tekshirish
        content_type = image.content_type
        if content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rasm turi qabul qilinmaydi. Qabul qilinadigan turlar: {settings.ALLOWED_IMAGE_TYPES}"
            )

        # Rasmni saqlash
        file_extension = os.path.splitext(image.filename)[1]
        filename = f"worker_{db_worker.id}{file_extension}"
        file_path = FilePath(settings.WORKER_IMAGES_DIR) / filename

        # Papkani yaratish (agar mavjud bo'lmasa)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Rasmni yozish
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Rasmni worker ma'lumotlariga qo'shish
        image_url = f"{settings.MEDIA_URL}uploads/workers/{filename}"
        db_worker = worker_crud.update_worker_image(db, worker_id=db_worker.id, image_path=image_url)

    return db_worker


@router.get("/search", response_model=List[Worker])
async def search_workers(
        skills: Optional[List[str]] = Query(None, description="Ko'nikmalar ro'yxati"),
        languages: Optional[List[str]] = Query(None, description="Tillar ro'yxati"),
        payment_type: Optional[str] = Query(None, description="To'lov turi"),
        gender: Optional[str] = Query(None, description="Jinsi"),
        min_payment: Optional[int] = Query(None, description="Minimal to'lov"),
        max_payment: Optional[int] = Query(None, description="Maksimal to'lov"),
        location: Optional[str] = Query(None, description="Lokatsiya (format: 'latitude,longitude')"),
        distance: Optional[float] = Query(None, description="Masofa (km)"),
        skip: int = Query(0, description="O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(20, description="Qaytariladigan ma'lumotlar soni"),
        db: Session = Depends(get_db),
) -> Any:
    """
    Ishchilarni qidirish

    Turli parametrlar bo'yicha ishchilarni qidirish imkonini beradi
    """
    # Qidirish parametrlarini yaratish
    search_params = WorkerSearchParams(
        skills=skills,
        languages=languages,
        payment_type=payment_type,
        gender=gender,
        min_payment=min_payment,
        max_payment=max_payment,
        location=location,
        distance=distance,
    )

    # Qidirish
    workers = worker_crud.search_workers(
        db, search_params=search_params, skip=skip, limit=limit
    )

    return workers


@router.get("/stats", response_model=WorkerStats)
async def get_worker_statistics(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Ishchilar haqida statistika ma'lumotlarini olish
    """
    stats = worker_crud.get_worker_statistics(db)
    return stats


@router.get("/{worker_id}", response_model=WorkerWithFeedbacks)
async def read_worker(
        worker_id: int = Path(..., description="Ishchi ID si"),
        db: Session = Depends(get_db),
) -> Any:
    """
    Ishchi ma'lumotlarini olish

    Berilgan ID bo'yicha ishchi ma'lumotlarini va uning haqidagi fikrlarni qaytaradi
    """
    worker = worker_crud.get_worker(db, worker_id=worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    # Fikrlarni olish
    feedbacks = feedback_crud.get_worker_feedbacks(db, worker_id=worker_id)

    # Response tayyorlash
    worker_with_feedbacks = WorkerWithFeedbacks.from_orm(worker)
    worker_with_feedbacks.feedbacks = feedbacks

    return worker_with_feedbacks


@router.put("/{worker_id}", response_model=Worker)
async def update_worker(
        worker_id: int,
        worker_in: WorkerUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Ishchi ma'lumotlarini yangilash

    Berilgan ID bo'yicha ishchi ma'lumotlarini yangilaydi
    """
    worker = worker_crud.get_worker(db, worker_id=worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    # Telefon raqami unique bo'lishi kerak
    if worker_in.phone and worker_in.phone != worker.phone:
        db_worker_by_phone = worker_crud.get_worker_by_phone(db, phone=worker_in.phone)
        if db_worker_by_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telefon raqami ro'yxatdan o'tgan"
            )

    return worker_crud.update_worker(db=db, worker_id=worker_id, worker_update=worker_in)


@router.patch("/{worker_id}/location", response_model=Worker)
async def update_worker_location(
        worker_id: int,
        location: WorkerLocation,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Ishchi lokatsiyasini yangilash

    Berilgan ID bo'yicha ishchi lokatsiyasini yangilaydi
    """
    worker = worker_crud.get_worker(db, worker_id=worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    return worker_crud.update_worker_location(db=db, worker_id=worker_id, location=location)


@router.patch("/{worker_id}/image", response_model=Worker)
async def update_worker_image(
        worker_id: int,
        image: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Ishchi rasmini yangilash

    Berilgan ID bo'yicha ishchi rasmini yangilaydi
    """
    worker = worker_crud.get_worker(db, worker_id=worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    # Rasm mime turini tekshirish
    content_type = image.content_type
    if content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rasm turi qabul qilinmaydi. Qabul qilinadigan turlar: {settings.ALLOWED_IMAGE_TYPES}"
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
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Rasmni yozish
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # Rasmni worker ma'lumotlariga qo'shish
    image_url = f"{settings.MEDIA_URL}uploads/workers/{filename}"
    return worker_crud.update_worker_image(db=db, worker_id=worker_id, image_path=image_url)


@router.patch("/{worker_id}/toggle-status", status_code=status.HTTP_200_OK)
async def toggle_worker_status(
        worker_id: int,
        is_active: bool = Body(..., embed=True),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> dict:

    worker = worker_crud.get_worker(db, worker_id=worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    # Status o'zgartirish
    updated_worker = worker_crud.update_worker_status(
        db=db,
        worker_id=worker_id,
        is_active=is_active
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ishchi statusini o'zgartirishda xatolik yuz berdi"
        )
@router.delete("/{worker_id}", status_code=status.HTTP_200_OK)
async def delete_worker(
        worker_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> dict:  # Dict qaytaradi
    """
    Ishchini o'chirish

    Berilgan ID bo'yicha ishchini o'chiradi
    """
    worker = worker_crud.get_worker(db, worker_id=worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    # Ishchiga bog'langan rasmni o'chirish
    if worker.image:
        image_path = FilePath(settings.BASE_DIR) / worker.image.lstrip('/')
        if os.path.exists(image_path):
            os.remove(image_path)

    success = worker_crud.delete_worker(db=db, worker_id=worker_id)

    if success:
        return {"status": "success", "message": "Ishchi muvaffaqiyatli o'chirildi", "id": worker_id}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ishchini o'chirishda xatolik yuz berdi"
        )


@router.get("/top-rated", response_model=List[Dict[str, Any]])
async def get_top_rated_workers(
    limit: int = Query(10, description="Qaytariladigan ma'lumotlar soni"),
    db: Session = Depends(get_db),
):
    """Eng yuqori reytingli ishchilarni olish"""
    return feedback_crud.get_top_rated_workers(db, limit=limit)