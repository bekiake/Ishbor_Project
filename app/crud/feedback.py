"""
Feedback CRUD operatsiyalari

Feedback modeli uchun CRUD (Create, Read, Update, Delete) operatsiyalari
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Feedback, Worker, User
from app.schemas.schemas import FeedbackCreate, FeedbackUpdate


def get_feedback(db: Session, feedback_id: int) -> Optional[Feedback]:
    """
    ID bo'yicha fikrni olish

    Args:
        db: Database session
        feedback_id: Fikr ID si

    Returns:
        Optional[Feedback]: Fikr ma'lumotlari yoki None
    """
    return db.query(Feedback).filter(Feedback.id == feedback_id).first()


def get_worker_feedbacks(
    db: Session, worker_id: int, skip: int = 0, limit: int = 100, is_active: bool = True
) -> List[Feedback]:
    
    query = db.query(Feedback).filter(Feedback.worker_id == worker_id)

    return query.order_by(Feedback.create_at.desc()).offset(skip).limit(limit).all()


def get_user_feedbacks(
    db: Session, user_id: int, skip: int = 0, limit: int = 100, is_active: bool = True
) -> List[Feedback]:
    """
    Foydalanuvchi qoldirgan fikrlarni olish

    Args:
        db: Database session
        user_id: Foydalanuvchi ID si
        skip: O'tkazib yuborish uchun ma'lumotlar soni
        limit: Qaytariladigan ma'lumotlar soni
        is_active: Faqat faol fikrlarni qaytarish

    Returns:
        List[Feedback]: Fikrlar ro'yxati
    """
    query = db.query(Feedback).filter(Feedback.user_id == user_id)

    if is_active:
        query = query.filter(Feedback.is_active == True)

    return query.order_by(Feedback.create_at.desc()).offset(skip).limit(limit).all()


def get_worker_average_rating(db: Session, worker_id: int) -> float:
    """
    Ishchining o'rtacha reytingini olish

    Args:
        db: Database session
        worker_id: Ishchi ID si

    Returns:
        float: O'rtacha reyting
    """
    result = db.query(func.avg(Feedback.rate).label("average_rating")).filter(
        Feedback.worker_id == worker_id,
        Feedback.is_active == True
    ).scalar()

    return float(result) if result else 0.0


def get_recent_feedbacks(
    db: Session, skip: int = 0, limit: int = 10, is_active: bool = True
) -> List[Feedback]:
    """
    Eng so'nggi fikrlarni olish

    Args:
        db: Database session
        skip: O'tkazib yuborish uchun ma'lumotlar soni
        limit: Qaytariladigan ma'lumotlar soni
        is_active: Faqat faol fikrlarni qaytarish

    Returns:
        List[Feedback]: Fikrlar ro'yxati
    """
    query = db.query(Feedback)

    if is_active:
        query = query.filter(Feedback.is_active == True)

    return query.order_by(Feedback.create_at.desc()).offset(skip).limit(limit).all()


def create_feedback(db: Session, user_id: int,feedback: FeedbackCreate) -> Feedback:
    """
    Yangi fikr yaratish

    Args:
        db: Database session
        feedback: Fikr ma'lumotlari

    Returns:
        Feedback: Yaratilgan fikr
    """
    db_feedback = Feedback(
        worker_id=feedback.worker_id,
        user_id=user_id,
        rate=feedback.rate,
        text=feedback.text,
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def update_feedback(
    db: Session, feedback_id: int, feedback_update: FeedbackUpdate
) -> Optional[Feedback]:
    """
    Fikr ma'lumotlarini yangilash

    Args:
        db: Database session
        feedback_id: Fikr ID si
        feedback_update: Yangilanayotgan ma'lumotlar

    Returns:
        Optional[Feedback]: Yangilangan fikr ma'lumotlari yoki None
    """
    db_feedback = get_feedback(db, feedback_id)
    if db_feedback:
        update_data = feedback_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_feedback, field, value)
        db.commit()
        db.refresh(db_feedback)
    return db_feedback


def delete_feedback(db: Session, feedback_id: int) -> bool:
    """
    Fikrni o'chirish

    Args:
        db: Database session
        feedback_id: Fikr ID si

    Returns:
        bool: O'chirish muvaffaqiyatli bo'lsa True, aks holda False
    """
    db_feedback = get_feedback(db, feedback_id)
    if db_feedback:
        db.delete(db_feedback)
        db.commit()
        return True
    return False


def deactivate_feedback(db: Session, feedback_id: int) -> Optional[Feedback]:
    """
    Fikrni deaktivatsiya qilish

    Args:
        db: Database session
        feedback_id: Fikr ID si

    Returns:
        Optional[Feedback]: Yangilangan fikr ma'lumotlari yoki None
    """
    db_feedback = get_feedback(db, feedback_id)
    if db_feedback:
        db_feedback.is_active = False
        db.commit()
        db.refresh(db_feedback)
    return db_feedback


def get_feedback_statistics(db: Session) -> Dict[str, Any]:
    """
    Fikrlar haqida statistika ma'lumotlarini olish

    Args:
        db: Database session

    Returns:
        Dict[str, Any]: Statistika ma'lumotlari
    """
    # Umumiy fikrlar soni
    total_feedbacks = db.query(Feedback).count()

    # Faol fikrlar soni
    active_feedbacks = db.query(Feedback).filter(Feedback.is_active == True).count()

    # O'rtacha reyting
    average_rating = db.query(func.avg(Feedback.rate)).scalar() or 0

    # Reyting taqsimoti
    rating_distribution = {}
    rating_counts = db.query(
        Feedback.rate, func.count(Feedback.id)
    ).group_by(Feedback.rate).all()

    for rate, count in rating_counts:
        rating_distribution[str(rate)] = count

    # So'nggi fikrlar
    recent_feedbacks = get_recent_feedbacks(db, limit=5)

    return {
        "total_feedbacks": total_feedbacks,
        "active_feedbacks": active_feedbacks,
        "average_rating": float(average_rating),
        "rating_distribution": rating_distribution,
        "recent_feedbacks": recent_feedbacks,
    }


def check_user_feedback_for_worker(
    db: Session, worker_id: int, user_id: int
) -> Optional[Feedback]:
    """
    Foydalanuvchi berilgan ishchi haqida fikr qoldirganini tekshirish

    Args:
        db: Database session
        worker_id: Ishchi ID si
        user_id: Foydalanuvchi ID si

    Returns:
        Optional[Feedback]: Fikr ma'lumotlari yoki None
    """
    return db.query(Feedback).filter(
        Feedback.worker_id == worker_id,
        Feedback.user_id == user_id,
        Feedback.is_active == True
    ).first()


def get_top_rated_workers(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Eng yuqori reytingli ishchilarni olish

    Args:
        db: Database session
        limit: Qaytariladigan ma'lumotlar soni

    Returns:
        List[Dict[str, Any]]: Eng yuqori reytingli ishchilar ma'lumotlari
    """
    result = db.query(
        Worker,
        func.avg(Feedback.rate).label("average_rating"),
        func.count(Feedback.id).label("feedback_count")
    ).join(Feedback, Worker.id == Feedback.worker_id
    ).group_by(Worker.id
    ).having(func.count(Feedback.id) >= 3  # Kamida 3 ta fikr bo'lishi kerak
    ).order_by(
        func.avg(Feedback.rate).desc()
    ).limit(limit).all()

    top_workers = []
    for worker, avg_rating, feedback_count in result:
        top_workers.append({
            "id": worker.id,
            "name": worker.name,
            "telegram_id": worker.telegram_id,
            "image": worker.image,
            "skills": worker.get_skills_list(),
            "average_rating": float(avg_rating),
            "feedback_count": feedback_count
        })

    return top_workers