"""
Worker CRUD operatsiyalari

Worker modeli uchun CRUD (Create, Read, Update, Delete) operatsiyalari
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
import math

from app.models.models import Worker, Feedback
from app.schemas.schemas import WorkerCreate, WorkerUpdate, WorkerLocation, WorkerSearchParams


def get_worker(db: Session, worker_id: int) -> Optional[Worker]:
    """
    ID bo'yicha ishchini olish

    Args:
        db: Database session
        worker_id: Ishchi ID si

    Returns:
        Optional[Worker]: Ishchi ma'lumotlari yoki None
    """
    return db.query(Worker).filter(Worker.id == worker_id).first()


def get_worker_by_telegram_id(db: Session, telegram_id: str) -> Optional[Worker]:
    """
    Telegram ID bo'yicha ishchini olish

    Args:
        db: Database session
        telegram_id: Ishchi Telegram ID si

    Returns:
        Optional[Worker]: Ishchi ma'lumotlari yoki None
    """
    return db.query(Worker).filter(Worker.telegram_id == telegram_id).first()


def get_worker_by_phone(db: Session, phone: str) -> Optional[Worker]:
    """
    Telefon raqami bo'yicha ishchini olish

    Args:
        db: Database session
        phone: Ishchi telefon raqami

    Returns:
        Optional[Worker]: Ishchi ma'lumotlari yoki None
    """
    return db.query(Worker).filter(Worker.phone == phone).first()


def get_workers(
        db: Session, skip: int = 0, limit: int = 100, is_active: bool = True
) -> List[Worker]:
    """
    Ishchilar ro'yxatini olish

    Args:
        db: Database session
        skip: O'tkazib yuborish uchun ma'lumotlar soni
        limit: Qaytariladigan ma'lumotlar soni
        is_active: Faqat faol ishchilarni qaytarish

    Returns:
        List[Worker]: Ishchilar ro'yxati
    """
    query = db.query(Worker)

    if is_active:
        query = query.filter(Worker.is_active == True)

    return query.offset(skip).limit(limit).all()


def create_worker(db: Session, worker: WorkerCreate) -> Worker:
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
    db.commit()
    db.refresh(db_worker)

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


def update_worker(db: Session, worker_id: int, worker_update: WorkerUpdate) -> Optional[Worker]:
    """
    Ishchi ma'lumotlarini yangilash

    Args:
        db: Database session
        worker_id: Ishchi ID si
        worker_update: Yangilanayotgan ma'lumotlar

    Returns:
        Optional[Worker]: Yangilangan ishchi ma'lumotlari yoki None
    """
    db_worker = get_worker(db, worker_id)
    if db_worker:
        update_data = worker_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_worker, field, value)
        db.commit()
        db.refresh(db_worker)
    return db_worker


def update_worker_location(
        db: Session, worker_id: int, location: WorkerLocation
) -> Optional[Worker]:
    """
    Ishchi lokatsiyasini yangilash

    Args:
        db: Database session
        worker_id: Ishchi ID si
        location: Yangi lokatsiya ma'lumotlari

    Returns:
        Optional[Worker]: Yangilangan ishchi ma'lumotlari yoki None
    """
    db_worker = get_worker(db, worker_id)
    if db_worker:
        db_worker.location = f"{location.latitude},{location.longitude}"
        db.commit()
        db.refresh(db_worker)
    return db_worker


def update_worker_image(db: Session, worker_id: int, image_path: str) -> Optional[Worker]:

    db_worker = get_worker(db, worker_id)
    if db_worker:
        db_worker.image = image_path
        db.commit()
        db.refresh(db_worker)
    return db_worker


def update_worker_status(db: Session, worker_id: int, is_active: bool) -> Optional[Worker]:

    db_worker = get_worker(db, worker_id=worker_id)
    if db_worker:
        db_worker.is_active = is_active
        db.commit()
        db.refresh(db_worker)
    return db_worker

def delete_worker(db: Session, worker_id: int) -> bool:

    db_worker = get_worker(db, worker_id)
    if db_worker:
        db.delete(db_worker)
        db.commit()
        return True
    return False


def deactivate_worker(db: Session, worker_id: int) -> Optional[Worker]:

    db_worker = get_worker(db, worker_id)
    if db_worker:
        db_worker.is_active = False
        db.commit()
        db.refresh(db_worker)
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


def search_workers(
        db: Session,
        search_params: WorkerSearchParams,
        skip: int = 0,
        limit: int = 100
) -> List[Worker]:

    query = db.query(Worker).filter(Worker.is_active == True)

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
    workers = query.offset(skip).limit(limit).all()

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


def get_worker_statistics(db: Session) -> Dict[str, Any]:

    # Umumiy ishchilar soni
    total_workers = db.query(Worker).count()

    # Faol ishchilar soni
    active_workers = db.query(Worker).filter(Worker.is_active == True).count()

    # O'rtacha reyting
    average_rating = db.query(func.avg(Feedback.rate)).scalar() or 0

    # To'lov turi bo'yicha taqsimlash
    payment_distribution = {}
    payment_counts = db.query(
        Worker.payment_type, func.count(Worker.id)
    ).group_by(Worker.payment_type).all()

    for payment_type, count in payment_counts:
        payment_distribution[payment_type or "Unknown"] = count

    # Jins bo'yicha taqsimlash
    gender_distribution = {}
    gender_counts = db.query(
        Worker.gender, func.count(Worker.id)
    ).group_by(Worker.gender).all()

    for gender, count in gender_counts:
        gender_distribution[gender or "Unknown"] = count

    return {
        "total_workers": total_workers,
        "active_workers": active_workers,
        "average_rating": float(average_rating),
        "payment_distribution": payment_distribution,
        "gender_distribution": gender_distribution,
    }