from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import aliased
from sqlalchemy import func
from app.models.models import Feedback, Worker, User
from app.schemas.schemas import FeedbackCreate, FeedbackResponse

# Asynchronous CRUD for Feedback

async def get_feedback(db: AsyncSession, feedback_id: int) -> Optional[Feedback]:
    result = await db.execute(select(Feedback).filter(Feedback.id == feedback_id))
    return result.scalar_one_or_none()


async def get_worker_with_feedbacks(db: AsyncSession, worker_id: int) -> Optional[Worker]:
    worker = await db.execute(select(Worker).filter(Worker.id == worker_id))
    worker = worker.scalar_one_or_none()
    if not worker:
        return None

    UserAlias = aliased(User)
    feedbacks = await db.execute(
        select(
            Feedback.id.label("feedback_id"),
            UserAlias.name.label("user_name"),
            Feedback.rate,
            Feedback.text,
            Feedback.create_at
        )
        .join(UserAlias, Feedback.user_id == UserAlias.id)
        .filter(Feedback.worker_id == worker_id)
        .order_by(Feedback.create_at.desc())
    )
    feedbacks = feedbacks.scalars().all()

    # Attach feedbacks to worker
    worker.feedbacks = [
        FeedbackResponse(
            feedback_id=feedback.feedback_id,
            user_name=feedback.user_name,
            rate=feedback.rate,
            text=feedback.text,
            create_at=feedback.create_at,
        )
        for feedback in feedbacks
    ]

    return worker

async def get_user_feedbacks(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100, is_active: bool = True
) -> List[Feedback]:
    query = select(Feedback).filter(Feedback.user_id == user_id)
    if is_active:
        query = query.filter(Feedback.is_active == True)

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def get_worker_average_rating(db: AsyncSession, worker_id: int) -> float:
    result = await db.execute(
        select(func.avg(Feedback.rate).label("average_rating"))
        .filter(Feedback.worker_id == worker_id, Feedback.is_active == True)
    )
    avg_rating = result.scalar_one_or_none()
    return float(avg_rating) if avg_rating else 0.0

async def get_recent_feedbacks(
    db: AsyncSession, skip: int = 0, limit: int = 10, is_active: bool = True
) -> List[Feedback]:
    query = select(Feedback)
    if is_active:
        query = query.filter(Feedback.is_active == True)

    result = await db.execute(query.order_by(Feedback.create_at.desc()).offset(skip).limit(limit))
    return result.scalars().all()

async def create_feedback(db: AsyncSession, user_id: int, feedback: FeedbackCreate) -> Feedback:
    db_feedback = Feedback(
        worker_id=feedback.worker_id,
        user_id=user_id,
        rate=feedback.rate,
        text=feedback.text,
    )
    db.add(db_feedback)
    await db.commit()
    await db.refresh(db_feedback)
    return db_feedback

async def delete_feedback(db: AsyncSession, feedback_id: int) -> bool:
    db_feedback = await get_feedback(db, feedback_id)
    if db_feedback:
        await db.delete(db_feedback)
        await db.commit()
        return True
    return False

async def deactivate_feedback(db: AsyncSession, feedback_id: int) -> Optional[Feedback]:
    db_feedback = await get_feedback(db, feedback_id)
    if db_feedback:
        db_feedback.is_active = False
        await db.commit()
        await db.refresh(db_feedback)
    return db_feedback

async def get_feedback_statistics(db: AsyncSession) -> Dict[str, Any]:
    total_feedbacks = await db.execute(select(func.count(Feedback.id)))
    total_feedbacks = total_feedbacks.scalar_one_or_none()

    active_feedbacks = await db.execute(select(func.count(Feedback.id)).filter(Feedback.is_active == True))
    active_feedbacks = active_feedbacks.scalar_one_or_none()

    average_rating = await db.execute(select(func.avg(Feedback.rate)))
    average_rating = average_rating.scalar_one_or_none() or 0

    rating_distribution = {}
    rating_counts = await db.execute(
        select(Feedback.rate, func.count(Feedback.id)).group_by(Feedback.rate)
    )
    for rate, count in rating_counts:
        rating_distribution[str(rate)] = count

    recent_feedbacks = await get_recent_feedbacks(db, limit=5)

    return {
        "total_feedbacks": total_feedbacks,
        "active_feedbacks": active_feedbacks,
        "average_rating": float(average_rating),
        "rating_distribution": rating_distribution,
        "recent_feedbacks": recent_feedbacks,
    }

async def check_user_feedback_for_worker(
    db: AsyncSession, worker_id: int, user_id: int
) -> Optional[Feedback]:
    result = await db.execute(
        select(Feedback)
        .filter(Feedback.worker_id == worker_id, Feedback.user_id == user_id, Feedback.is_active == True)
    )
    return result.scalar_one_or_none()

async def get_top_rated_workers(db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(
            Worker,
            func.avg(Feedback.rate).label("average_rating"),
            func.count(Feedback.id).label("feedback_count")
        )
        .join(Feedback, Worker.id == Feedback.worker_id)
        .group_by(Worker.id)
        .having(func.count(Feedback.id) >= 3)
        .order_by(func.avg(Feedback.rate).desc())
        .limit(limit)
    )

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
