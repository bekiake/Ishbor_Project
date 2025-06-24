from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from app.models.models import Feedback, Worker, User
from app.schemas.schemas import FeedbackCreate, FeedbackResponse


# Get a single feedback by id
async def get_feedback(db: AsyncSession, feedback_id: int) -> Optional[Feedback]:
    result = await db.execute(
        select(Feedback).filter(Feedback.id == feedback_id)
    )
    return result.scalar_one_or_none()


# Get a worker along with its feedbacks
async def get_worker_with_feedbacks(
    db: AsyncSession, worker_id: int
) -> Optional[Worker]:
    worker_result = await db.execute(
        select(Worker).filter(Worker.id == worker_id)
    )
    worker = worker_result.scalar_one_or_none()
    if not worker:
        return None

    UserAlias = aliased(User)
    feedbacks_result = await db.execute(
        select(
            Feedback.id.label("feedback_id"),
            UserAlias.name.label("user_name"),
            Feedback.rate,
            Feedback.text,
            Feedback.create_at
        )
        .join(UserAlias, Feedback.user_id == UserAlias.id)
        .filter(
            Feedback.worker_id == worker_id,
            Feedback.is_active == True
        )
        .order_by(Feedback.create_at.desc())
    )
    feedbacks_rows = feedbacks_result.fetchall()

    worker.feedbacks = [
        FeedbackResponse(
            feedback_id=row.feedback_id,
            user_name=row.user_name,
            rate=row.rate,
            text=row.text,
            create_at=row.create_at,
        )
        for row in feedbacks_rows
    ]
    return worker


# Get user feedbacks
async def get_user_feedbacks(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100, is_active: bool = True
) -> List[Feedback]:
    query = select(Feedback).filter(Feedback.user_id == user_id)
    if is_active:
        query = query.filter(Feedback.is_active == True)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


# Get average rating for a worker
async def get_worker_average_rating(db: AsyncSession, worker_id: int) -> float:
    result = await db.execute(
        select(func.avg(Feedback.rate))
        .filter(Feedback.worker_id == worker_id, Feedback.is_active == True)
    )
    avg_rating = result.scalar_one_or_none()
    return float(avg_rating) if avg_rating else 0.0


# Get recent feedbacks
async def get_recent_feedbacks(
    db: AsyncSession, skip: int = 0, limit: int = 10, is_active: bool = True
) -> List[Feedback]:
    query = select(Feedback)
    if is_active:
        query = query.filter(Feedback.is_active == True)

    result = await db.execute(
        query.order_by(Feedback.create_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


# Create new feedback
async def create_feedback(db: AsyncSession, user_id: int, feedback: FeedbackCreate) -> Feedback:
    db_feedback = Feedback(
        worker_id=feedback.worker_id,
        user_id=user_id,
        rate=feedback.rate,
        text=feedback.text,
        is_active=True  # Defaulting to True
    )
    db.add(db_feedback)
    await db.commit()
    await db.refresh(db_feedback)
    return db_feedback


# Delete feedback
async def delete_feedback(db: AsyncSession, feedback_id: int) -> bool:
    db_feedback = await get_feedback(db, feedback_id)
    if db_feedback:
        await db.delete(db_feedback)
        await db.commit()
        return True
    return False


# Deactivate feedback
async def deactivate_feedback(db: AsyncSession, feedback_id: int) -> Optional[Feedback]:
    db_feedback = await get_feedback(db, feedback_id)
    if db_feedback:
        db_feedback.is_active = False
        await db.commit()
        await db.refresh(db_feedback)
    return db_feedback


# Get feedback statistics
async def get_feedback_statistics(db: AsyncSession) -> Dict[str, Any]:
    total_feedbacks = (await db.execute(select(func.count(Feedback.id)))).scalar_one_or_none() or 0
    active_feedbacks = (await db.execute(
        select(func.count(Feedback.id)).filter(Feedback.is_active == True)
    )).scalar_one_or_none() or 0

    average_rating = (await db.execute(
        select(func.avg(Feedback.rate))
    )).scalar_one_or_none() or 0.0

    # Rating distribution
    rating_distribution: Dict[str, int] = {}
    rating_rows = (await db.execute(
        select(Feedback.rate, func.count(Feedback.id)).group_by(Feedback.rate)
    )).fetchall()
    for rate, count in rating_rows:
        rating_distribution[str(rate)] = count

    recent_feedbacks = await get_recent_feedbacks(db, limit=5)

    return {
        "total_feedbacks": total_feedbacks,
        "active_feedbacks": active_feedbacks,
        "average_rating": float(average_rating),
        "rating_distribution": rating_distribution,
        "recent_feedbacks": recent_feedbacks,
    }


# Check if a user already left a feedback for a particular worker
async def check_user_feedback_for_worker(
    db: AsyncSession, worker_id: int, user_id: int
) -> Optional[Feedback]:
    result = await db.execute(
        select(Feedback)
        .filter(
            Feedback.worker_id == worker_id,
            Feedback.user_id == user_id,
            Feedback.is_active == True
        )
    )
    return result.scalar_one_or_none()


# Get top-rated workers
async def get_top_rated_workers(db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(
            Worker,
            func.avg(Feedback.rate).label("average_rating"),
            func.count(Feedback.id).label("feedback_count")
        )
        .join(Feedback, Worker.id == Feedback.worker_id)
        .filter(Feedback.is_active == True)
        .group_by(Worker.id)
        .having(func.count(Feedback.id) >= 3)
        .order_by(func.avg(Feedback.rate).desc())
        .limit(limit)
    )
    top_workers: List[Dict[str, Any]] = []
    for worker, avg_rating, feedback_count in result:
        top_workers.append(
            {
                "id": worker.id,
                "name": worker.name,
                "telegram_id": worker.telegram_id,
                "image": worker.image,
                "skills": worker.get_skills_list(),
                "average_rating": float(avg_rating),
                "feedback_count": feedback_count,
            }
        )
    return top_workers
