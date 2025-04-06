from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, and_
import math

from app.models.models import Worker, Feedback
from app.schemas.schemas import WorkerCreate, WorkerUpdate, WorkerLocation, WorkerSearchParams


async def get_worker(db: AsyncSession, worker_id: int) -> Optional[Worker]:
    result = await db.execute(select(Worker).filter(Worker.id == worker_id))
    return result.scalar_one_or_none()


async def get_worker_by_telegram_id(db: AsyncSession, telegram_id: str) -> Optional[Worker]:
    result = await db.execute(select(Worker).filter(Worker.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_worker_by_phone(db: AsyncSession, phone: str) -> Optional[Worker]:
    result = await db.execute(select(Worker).filter(Worker.phone == phone))
    return result.scalar_one_or_none()


async def get_workers(
        db: AsyncSession, skip: int = 0, limit: int = 100, is_active: bool = True
) -> List[Worker]:
    query = select(Worker).offset(skip).limit(limit)

    if is_active:
        query = query.filter(Worker.is_active == True)

    result = await db.execute(query)
    return result.scalars().all()


async def create_worker(db: AsyncSession, worker: WorkerCreate) -> Worker:
    db_worker = Worker(
        telegram_id=worker.telegram_id,
        name=worker.name,
        age=worker.age,
        phone=worker.phone,
        gender=worker.gender,
        payment_type=worker.payment_type,
        daily_payment=worker.daily_payment,
        languages=worker.languages,
        skills=worker.skills,
        location=worker.location,
    )
    db.add(db_worker)
    await db.commit()
    await db.refresh(db_worker)

    if db_worker.languages:
        db_worker.languages_list = [lang.strip() for lang in db_worker.languages.split(',')]
    else:
        db_worker.languages_list = []

    if db_worker.skills:
        db_worker.skills_list = [skill.strip() for skill in db_worker.skills.split(',')]
    else:
        db_worker.skills_list = []

    if db_worker.location:
        try:
            lat, lng = map(float, db_worker.location.split(','))
            db_worker.location_coords = {"latitude": lat, "longitude": lng}
        except (ValueError, TypeError):
            db_worker.location_coords = None
    else:
        db_worker.location_coords = None

    return db_worker


async def update_worker(db: AsyncSession, worker_id: int, worker_update: WorkerUpdate) -> Optional[Worker]:
    db_worker = await get_worker(db, worker_id)
    if db_worker:
        update_data = worker_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_worker, field, value)
        await db.commit()
        await db.refresh(db_worker)
    return db_worker


async def update_worker_location(
        db: AsyncSession, worker_id: int, location: WorkerLocation
) -> Optional[Worker]:
    db_worker = await get_worker(db, worker_id)
    if db_worker:
        db_worker.location = f"{location.latitude},{location.longitude}"
        await db.commit()
        await db.refresh(db_worker)
    return db_worker


async def update_worker_image(db: AsyncSession, worker_id: int, image_path: str) -> Optional[Worker]:
    db_worker = await get_worker(db, worker_id)
    if db_worker:
        db_worker.image = image_path
        await db.commit()
        await db.refresh(db_worker)
    return db_worker


async def update_worker_status(db: AsyncSession, worker_id: int, is_active: bool) -> Optional[Worker]:
    db_worker = await get_worker(db, worker_id)
    if db_worker:
        db_worker.is_active = is_active
        await db.commit()
        await db.refresh(db_worker)
    return db_worker


async def delete_worker(db: AsyncSession, worker_id: int) -> bool:
    db_worker = await get_worker(db, worker_id)
    if db_worker:
        await db.delete(db_worker)
        await db.commit()
        return True
    return False


async def deactivate_worker(db: AsyncSession, worker_id: int) -> Optional[Worker]:
    db_worker = await get_worker(db, worker_id)
    if db_worker:
        db_worker.is_active = False
        await db.commit()
        await db.refresh(db_worker)
    return db_worker


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Yer radiusi (km)
    R = 6371.0

    # Radianlarga aylantirish
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Farqlar
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance


async def search_workers(
        db: AsyncSession,
        search_params: WorkerSearchParams,
        skip: int = 0,
        limit: int = 100
) -> List[Worker]:
    query = select(Worker).filter(Worker.is_active == True)

    # Ko'nikmalar bo'yicha filtrlash
    if search_params.skills:
        skill_filters = []
        for skill in search_params.skills:
            skill_filters.append(Worker.skills.ilike(f'%{skill}%'))
        if skill_filters:
            query = query.filter(or_(*skill_filters))

    # Tillar bo'yicha filtrlash
    if search_params.languages:
        language_filters = []
        for language in search_params.languages:
            language_filters.append(Worker.languages.ilike(f'%{language}%'))
        if language_filters:
            query = query.filter(or_(*language_filters))

    # To'lov turi bo'yicha filtrlash
    if search_params.payment_type:
        query = query.filter(
            or_(
                Worker.payment_type == search_params.payment_type,
                Worker.payment_type == "barchasi"
            )
        )

    # Jins bo'yicha filtrlash
    if search_params.gender:
        query = query.filter(Worker.gender == search_params.gender)

    # To'lov miqdori bo'yicha filtrlash
    if search_params.min_payment is not None:
        query = query.filter(Worker.daily_payment >= search_params.min_payment)
    if search_params.max_payment is not None:
        query = query.filter(Worker.daily_payment <= search_params.max_payment)

    # Lokatsiya bo'yicha filtrlash
    # Agar lokatsiya va masofa berilgan bo'lsa, Python kodida filtrlash kerak
    result = await db.execute(query)
    workers = result.scalars().all()

    if search_params.location and search_params.distance:
        try:
            # Lokatsiya formatini tekshirish
            parts = search_params.location.split(',')
            if len(parts) != 2:
                return workers  # Noto'g'ri format bo'lsa, filtrsiz qaytarish

            # Qidiruv koordinatalari
            search_lat = float(parts[0].strip())
            search_lon = float(parts[1].strip())

            # Masofaga qarab filtrlash
            filtered_workers = []
            for worker in workers:
                if worker.location:
                    try:
                        lat, lon = worker.get_location_tuple()
                        if lat is not None and lon is not None:
                            distance = calculate_distance(search_lat, search_lon, lat, lon)
                            if distance <= search_params.distance:
                                filtered_workers.append(worker)
                    except (ValueError, TypeError):
                        pass  # Noto'g'ri koordinata formatini o'tkazib yuborish

            return filtered_workers
        except (ValueError, TypeError):
            # Xatolik yuz bersa, filtrsiz qaytarish
            return workers

    return workers


async def get_worker_statistics(db: AsyncSession) -> Dict[str, Any]:
    # Umumiy ishchilar soni
    total_workers = await db.execute(select(func.count(Worker.id)))
    total_workers = total_workers.scalar()

    # Faol ishchilar soni
    active_workers = await db.execute(select(func.count(Worker.id)).filter(Worker.is_active == True))
    active_workers = active_workers.scalar()

    # O'rtacha reyting
    average_rating = await db.execute(select(func.avg(Feedback.rate)))
    average_rating = average_rating.scalar() or 0

    # To'lov turi bo'yicha taqsimlash
    payment_distribution = {}
    payment_counts = await db.execute(
        select(Worker.payment_type, func.count(Worker.id))
        .group_by(Worker.payment_type)
    )
    payment_counts = payment_counts.all()

    for payment_type, count in payment_counts:
        payment_distribution[payment_type or "Unknown"] = count

    # Jins bo'yicha taqsimlash
    gender_distribution = {}
    gender_counts = await db.execute(
        select(Worker.gender, func.count(Worker.id))
        .group_by(Worker.gender)
    )
    gender_counts = gender_counts.all()

    for gender, count in gender_counts:
        gender_distribution[gender or "Unknown"] = count

    return {
        "total_workers": total_workers,
        "active_workers": active_workers,
        "average_rating": float(average_rating),
        "payment_distribution": payment_distribution,
        "gender_distribution": gender_distribution,
    }
