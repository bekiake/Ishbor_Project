from typing import Any, List, Optional, Dict
from fastapi import (
    APIRouter, Depends, HTTPException, status, Query,
    Form, UploadFile, File, Path, Body,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import aiofiles  # Asinxron fayl operatsiyalari uchun
import os
from pathlib import Path as FilePath
from ...core.security import get_current_user
from app.database import get_db as get_async_db  # Sizning get_db funksiyangiz
from app.schemas.schemas import (
    Worker, WorkerCreate, WorkerUpdate, WorkerWithFeedbacks,
    WorkerLocation, Feedback, WorkerSearchParams, WorkerStats, WorkerDetail
)
from app.crud import worker as worker_crud
from app.crud import feedback as feedback_crud
from app.crud import user as user_crud
from app.core.security import get_current_active_user
from app.core.settings import settings
from app.models import models

router = APIRouter()

@router.get("/", response_model=List[Worker])
async def read_workers(
        skip: int = Query(0, description="O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(100, description="Qaytariladigan ma'lumotlar soni"),
        is_active: bool = Query(True, description="Faqat faol ishchilarni qaytarish"),
        db: AsyncSession = Depends(get_async_db),
) -> Any:
    workers = await worker_crud.get_workers(db, skip=skip, limit=limit, is_active=is_active)
    return workers

@router.get("/me", response_model=dict)
async def read_worker_me(
        current_user: models.User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_async_db)
):
    telegram_id = current_user.telegram_id
    worker = await worker_crud.get_worker_by_telegram_id(db, telegram_id)
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )

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
        db: AsyncSession = Depends(get_async_db),
        current_user: models.User = Depends(get_current_active_user),
) -> Any:
    db_worker = await worker_crud.get_worker_by_telegram_id(db, telegram_id=telegram_id)
    if db_worker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram ID ro'yxatdan o'tgan"
        )

    if phone:
        db_worker_by_phone = await worker_crud.get_worker_by_phone(db, phone=phone)
        if db_worker_by_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telefon raqami ro'yxatdan o'tgan"
            )

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

    db_worker = await worker_crud.create_worker(db=db, worker=worker_data)

    if image:
        content_type = image.content_type
        if content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rasm turi qabul qilinmaydi. Qabul qilinadigan turlar: {settings.ALLOWED_IMAGE_TYPES}"
            )

        file_extension = os.path.splitext(image.filename)[1]
        filename = f"worker_{db_worker.id}{file_extension}"
        file_path = FilePath(settings.WORKER_IMAGES_DIR) / filename
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        async with aiofiles.open(file_path, "wb") as buffer:
            content = await image.read()
            await buffer.write(content)

        image_url = f"{settings.MEDIA_URL}uploads/workers/{filename}"
        db_worker = await worker_crud.update_worker_image(db, worker_id=db_worker.id, image_path=image_url)

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
        db: AsyncSession = Depends(get_async_db),
) -> Any:
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

    workers = await worker_crud.search_workers(
        db, search_params=search_params, skip=skip, limit=limit
    )
    return workers


@router.get("/{worker_id}")
async def get_worker_detail(worker_id: int, db: AsyncSession = Depends(get_async_db)):
    stmt = select(models.Worker).filter(models.Worker.id == worker_id)
    
    # So'rovni bajarish va natijani olish
    result = await db.execute(stmt)  # So'rovni kutish
    workers = result.scalar_one_or_none()  # await kalit so'zini olib tashlang
    
    if not workers:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Feedbacklarni olish
    stmt = select(models.Feedback).filter(models.Feedback.worker_id == worker_id)
    result = await db.execute(stmt)  # So'rovni kutish
    feedbacks = result.scalars().all()
    
    # Feedbacklarni formatlash
    feedbacks_data = [
        {
            "id": feedback.id,
            "rate": feedback.rate,
            "text": feedback.text,
            "create_at": feedback.create_at,
            "update_at": feedback.update_at,
            "user_name": feedback.user.name if feedback.user else "Anonymous"
        }
        for feedback in feedbacks
    ]
    
    # Worker va feedbacklar bilan javob qaytarish
    return {
        "id": workers.id,
        "telegram_id": workers.telegram_id,
        "name": workers.name,
        "image": workers.image,
        "age": workers.age,
        "phone": workers.phone,
        "gender": workers.gender,
        "payment_type": workers.payment_type,
        "daily_payment": workers.daily_payment,
        "languages": workers.languages,
        "skills": workers.skills,
        "location": workers.location,
        "is_active": workers.is_active,
        "created_at": workers.created_at,
        "updated_at": workers.updated_at,
        "feedbacks": feedbacks_data if feedbacks else None
    }



@router.put("/{worker_id}", response_model=Worker)
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
        db: AsyncSession = Depends(get_async_db),
        current_user: models.User = Depends(get_current_active_user),
) -> Any:
    worker = await worker_crud.get_worker(db, worker_id=worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    if phone and phone != worker.phone:
        db_worker_by_phone = await worker_crud.get_worker_by_phone(db, phone=phone)
        if db_worker_by_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telefon raqami ro'yxatdan o'tgan"
            )

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
        worker.set_languages([lang.strip() for lang in languages.split(",")])
    if skills is not None:
        worker.set_skills([skill.strip() for skill in skills.split(",")])
    if latitude is not None and longitude is not None:
        worker.set_location(latitude, longitude)
    if is_active is not None:
        update_data["is_active"] = is_active

    worker_update = WorkerUpdate(**update_data)
    worker = await worker_crud.update_worker(db=db, worker_id=worker_id, worker_update=worker_update)

    if image:
        content_type = image.content_type
        if content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rasm turi qabul qilinmaydi. Qabul qilinadigan turlar: {settings.ALLOWED_IMAGE_TYPES}"
            )

        if worker.image:
            old_image_path = FilePath(settings.BASE_DIR) / worker.image.lstrip('/')
            if os.path.exists(old_image_path):
                os.remove(old_image_path)  # Bu sinxron, lekin keyinroq optimallashtirish mumkin

        file_extension = os.path.splitext(image.filename)[1]
        filename = f"worker_{worker_id}{file_extension}"
        file_path = FilePath(settings.WORKER_IMAGES_DIR) / filename
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        async with aiofiles.open(file_path, "wb") as buffer:
            content = await image.read()
            await buffer.write(content)

        image_url = f"{settings.MEDIA_URL}uploads/workers/{filename}"
        worker = await worker_crud.update_worker_image(db=db, worker_id=worker_id, image_path=image_url)

    return worker

@router.patch("/{worker_id}/toggle-status", status_code=status.HTTP_200_OK)
async def toggle_worker_status(
        worker_id: int,
        is_active: bool = Body(..., embed=True),
        db: AsyncSession = Depends(get_async_db),
        current_user: models.User = Depends(get_current_active_user),
) -> dict:
    worker = await worker_crud.get_worker(db, worker_id=worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    updated_worker = await worker_crud.update_worker_status(
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
        db: AsyncSession = Depends(get_async_db),
        current_user: models.User = Depends(get_current_active_user),
) -> dict:
    worker = await worker_crud.get_worker(db, worker_id=worker_id)
    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ishchi topilmadi"
        )

    if worker.image:
        image_path = FilePath(settings.BASE_DIR) / worker.image.lstrip('/')
        if os.path.exists(image_path):
            os.remove(image_path)  # Bu sinxron, lekin keyinroq optimallashtirish mumkin

    success = await worker_crud.delete_worker(db=db, worker_id=worker_id)

    if success:
        return {"status": "success", "message": "Ishchi muvaffaqiyatli o'chirildi", "id": worker_id}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ishchini o'chirishda xatolik yuz berdi"
        )