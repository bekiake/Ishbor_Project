from typing import Any, List, Optional, Dict
from fastapi import (
    APIRouter, Depends, HTTPException, Request, status, Query,
    Form, UploadFile, File, Path, Body,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from sqlalchemy.orm import selectinload
import aiofiles  # Asinxron fayl operatsiyalari uchun
import os
from pathlib import Path as FilePath
from ...core.security import get_current_user
from app.database import get_db as get_async_db  # Sizning get_db funksiyangiz
from app.schemas.schemas import (
    Worker, WorkerCreate, WorkerUpdate, WorkerWithFeedbacks,
    WorkerLocation, Feedback, WorkerSearchParams, WorkerStats, WorkerDetail, WorkerSimpleSchema
)
from app.crud import worker as worker_crud
from app.crud import feedback as feedback_crud
from app.crud import user as user_crud
from app.core.security import get_current_active_user
from app.core.settings import settings
from app.models import models

router = APIRouter()

@router.get("/", response_model=List[WorkerSimpleSchema])
async def read_workers(
        skip: int = Query(0, description="O'tkazib yuborish uchun ma'lumotlar soni"),
        limit: int = Query(100, description="Qaytariladigan ma'lumotlar soni"),
        is_active: bool = Query(True, description="Faqat faol ishchilarni qaytarish"),
        db: AsyncSession = Depends(get_async_db),
) -> Any:
    workers = await worker_crud.get_workers(db, skip=skip, limit=limit, is_active=is_active)
    result = []
    for worker in workers:
        image = f"https://admin.ishbozor.uz{worker.image}" if worker.image else None
        skills_list = [s.strip() for s in worker.skills.split(",")] if worker.skills else []
        languages_list = [l.strip() for l in worker.languages.split(",")] if worker.languages else []
        
        result.append(WorkerSimpleSchema(
            id=worker.id,
            name=worker.name,
            age=worker.age,
            gender=worker.gender,
            phone=worker.phone,
            location=worker.location,
            skills=skills_list,
            languages=languages_list,
            image=image,
        ))

    return result

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
        "about": worker.about,
        "age": worker.age,
        "phone": worker.phone,
        "gender": worker.gender,
        "payment_type": worker.payment_type,
        "daily_payment": worker.daily_payment,
        "languages": worker.languages,
        "skills": worker.skills,
        "location": worker.location,
        "image": f"https://admin.ishbozor.uz{worker.image}",
        "is_active": worker.is_active
    }
    return worker_data

@router.post("/with-image", response_model=Worker, status_code=status.HTTP_201_CREATED)
async def create_worker_with_image(
        telegram_id: str = Form(...),
        name: Optional[str] = Form(None),
        about: Optional[str] = Form(None),
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
        about=about,
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

# @router.get("/search", response_model=List[WorkerSimpleSchema])
# async def search_workers(
#         name: Optional[str] = Query(None, description="Ishchi ismi"),
#         skip: int = Query(0, description="O'tkazib yuborish uchun ma'lumotlar soni"),
#         limit: int = Query(20, description="Qaytariladigan ma'lumotlar soni"),
#         db: AsyncSession = Depends(get_async_db),
# ) -> Any:
#     search_params = WorkerSearchParams(
#         name=name
#     )

#     workers = await worker_crud.search_workers(
#         db, search_params=search_params, skip=skip, limit=limit
#     )
#     result = []
#     for worker in workers:
#         image = f"https://admin.ishbozor.uz{worker.image}" if worker.image else None
#         skills_list = [s.strip() for s in worker.skills.split(",")] if worker.skills else []
#         languages_list = [l.strip() for l in worker.languages.split(",")] if worker.languages else []
        
#         result.append(WorkerSimpleSchema(
#             id=worker.id,
#             name=worker.name,
#             age=worker.age,
#             gender=worker.gender,
#             phone=worker.phone,
#             location=worker.location,
#             skills=skills_list,
#             languages=languages_list,
#             image=image,
#         ))

#     return result

@router.get("/workers/filter/")
async def filter_workers(
    request: Request,
    name: Optional[str] = None,
    gender: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    raw_query_params = request.query_params
    skills = raw_query_params.getlist("skills[]")
    languages = raw_query_params.getlist("languages[]")
    age_range = raw_query_params.getlist("age_range[]")

    stmt = select(models.Worker).where(models.Worker.is_active == True)

    # Name yoki skill bo‘yicha filter
    if name:
        # Agar name kiritilgan bo'lsa, uni ism yoki skill nomi sifatida tekshiramiz
        name_condition = models.Worker.name.ilike(f"%{name}%")
        
        # Skill nomi bo‘yicha qidiruv
        skill_condition = models.Worker.skills.ilike(f"%{name}%")
        
        # Shartlarni OR orqali birlashtiramiz
        stmt = stmt.where(or_(name_condition, skill_condition))

    # Skills
    if skills and "barchasi" not in [s.lower() for s in skills]:
        skill_conditions = [models.Worker.skills.ilike(f"%{skill}%") for skill in skills]
        stmt = stmt.where(or_(*skill_conditions))

    # Languages
    if languages and "barchasi" not in [l.lower() for l in languages]:
        lang_conditions = [models.Worker.languages.ilike(f"%{lang}%") for lang in languages]
        stmt = stmt.where(or_(*lang_conditions))

    # Gender
    if gender and gender.lower() == "barchasi":
        stmt = stmt.where(models.Worker.gender.ilike(gender))

    # Age Range
    if age_range and "barchasi" not in [a.lower() for a in age_range]:
        age_conditions = []
        for range_str in age_range:
            try:
                min_age, max_age = map(int, range_str.split("-"))
                age_conditions.append(
                    models.Worker.age.between(min_age, max_age)
                )
            except ValueError:
                return {"error": f"age_range '{range_str}' must be like 25-35"}
        stmt = stmt.where(or_(*age_conditions))

    result = await db.execute(stmt)
    workers = result.scalars().all()

    return [
        {
            "id": w.id,
            "name": w.name,
            "age": w.age,
            "gender": w.gender,
            "phone": w.phone,
            "location": w.location,
            "skills": w.get_skills_list(),
            "languages": w.get_languages_list(),
            "image": f"https://admin.ishbozor.uz{w.image}" if w.image else None,
        }
        for w in workers
    ]



@router.get("/{worker_id}")
async def get_worker_with_feedbacks(worker_id: int, db: AsyncSession = Depends(get_async_db)):
    stmt = (
        select(models.Worker)
        .options(
            selectinload(models.Worker.feedbacks).selectinload(models.Feedback.user)
        )
        .filter(models.Worker.id == worker_id)
    )

    result = await db.execute(stmt)
    worker = result.scalar_one_or_none()

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # Rasm URL ni to'g'rilash
    if worker.image:
        worker.image = f"https://admin.ishbozor.uz{worker.image}"

    # Istasangiz bu yerdan return uchun JSON ko‘rinishga aylantirib yuborish mumkin:
    return {
        "id": worker.id,
        "name": worker.name,
        "about": worker.about,
        "image": worker.image,
        "age": worker.age,
        "phone": worker.phone,
        "gender": worker.gender,
        "payment_type": worker.payment_type,
        "daily_payment": worker.daily_payment,
        "languages": worker.get_languages_list(),
        "skills": worker.get_skills_list(),
        "location": worker.location,
        "created_at": str(worker.created_at),
        "feedbacks": [
            {
                "rate": fb.rate,
                "text": fb.text,
                "user": {
                    "id": fb.user.id,
                    "name": fb.user.name,
                    "telegram_id": fb.user.telegram_id,
                },
            }
            for fb in worker.feedbacks
        ]
    }


@router.put("/{worker_id}", response_model=Worker)
async def update_worker(
        worker_id: int,
        name: Optional[str] = Form(None),
        about: Optional[str] = Form(None),
        age: Optional[int] = Form(None),
        phone: Optional[str] = Form(None),
        gender: Optional[str] = Form(None),
        payment_type: Optional[str] = Form(None),
        daily_payment: Optional[int] = Form(None),
        languages: Optional[str] = Form(None),
        skills: Optional[str] = Form(None),
        location: Optional[str] = Form(None),
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
    if about is not None:
        update_data["about"] = about
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
    if location is not None:
        update_data["location"] = location
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
        worker.image = f"https://admin.ishbozor.uz{worker.image}"
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