from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db as get_async_db
from typing import List
from app.schemas.schemas import NewsOut
from app.models import models
from app.crud.news import get_all_news, get_news_by_id, mark_news_as_read_once, get_unread_news_count
from app.core.security import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[NewsOut])
async def api_get_all_news(db: AsyncSession = Depends(get_async_db)):
    return await get_all_news(db)

@router.get("/{news_id}", response_model=NewsOut)
async def api_get_news(news_id: int, db: AsyncSession = Depends(get_async_db)):

    news = await get_news_by_id(db, news_id)

    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news

@router.post("/{news_id}/read", response_model=NewsOut)
async def api_mark_news_as_read(
        news_id: int,
        current_user: models.User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_async_db),
):
    user_id = current_user.id

    news = await mark_news_as_read_once(db, news_id, user_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news

@router.get("/unread/count")
async def api_get_unread_news_count(
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(get_current_active_user),
):
    user_id = current_user.id
    count = await get_unread_news_count(db, user_id)
    return {"unread_news_count": count}