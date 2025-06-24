from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import models

async def get_all_news(db: AsyncSession) -> List[models.News]:
    result = await db.execute(
        select(models.News).order_by(models.News.id)
    )
    return result.scalars().all()

async def get_news_by_id(db: AsyncSession, news_id: int) -> Optional[models.News]:
    result = await db.execute(
        select(models.News).where(models.News.id == news_id)
    )
    return result.scalars().first()


async def mark_news_as_read_once(db: AsyncSession, news_id: int, user_id: int) -> models.News:
    # Allaqachon ko‘rganmi?
    result = await db.execute(
        select(models.NewsView).where(
            models.NewsView.news_id == news_id,
            models.NewsView.user_id == user_id
        )
    )
    existing = result.scalars().first()

    # Agar ko‘rgan bo‘lsa — shunchaki yangilikni qaytaramiz
    if existing:
        news_result = await db.execute(select(models.News).where(models.News.id == news_id))
        return news_result.scalars().first()

    # Yangi ko‘rish bo‘lsa — yozamiz
    db.add(models.NewsView(user_id=user_id, news_id=news_id))

    # View sonini oshiramiz
    news_result = await db.execute(select(models.News).where(models.News.id == news_id))
    news = news_result.scalars().first()
    if news:
        news.count_views += 1
        await db.commit()
        await db.refresh(news)
    return news


async def get_unread_news_count(db: AsyncSession, user_id: int) -> int:
    # O'qilgan yangilik IDlari
    result = await db.execute(
        select(models.NewsView.news_id).where(models.NewsView.user_id == user_id)
    )
    viewed_news_ids = result.scalars().all()

    # O'qilmagan yangiliklarni sanash
    query = select(func.count()).select_from(models.News)
    if viewed_news_ids:
        query = query.where(models.News.id.notin_(viewed_news_ids))

    result = await db.execute(query)
    return result.scalar_one()