from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import select, func
from app.models.models import User
from app.schemas.schemas import UserCreate, UserUpdate


# Get a user by ID
async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


# Get a user by Telegram ID
async def get_user_by_telegram_id(db: AsyncSession, telegram_id: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.telegram_id == telegram_id))
    return result.scalars().first()


# Get a list of users
async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


# Create a new user
async def create_user(db: AsyncSession, user: UserCreate) -> User:
    db_user = User(
        telegram_id=user.telegram_id,
        name=user.name,
        is_worker=user.is_worker,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# Update user by ID
async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[User]:
    db_user = await get_user(db, user_id)
    if db_user:
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        await db.commit()
        await db.refresh(db_user)
    return db_user


# Update user by Telegram ID
async def update_user_by_telegram_id(
        db: AsyncSession,
        telegram_id: str,
        user_update: UserUpdate
) -> Optional[User]:
    db_user = await get_user_by_telegram_id(db, telegram_id)
    if db_user:
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        await db.commit()
        await db.refresh(db_user)
    return db_user


# Delete user by ID
async def delete_user(db: AsyncSession, user_id: int) -> bool:
    db_user = await get_user(db, user_id)
    if db_user:
        await db.delete(db_user)
        await db.commit()
        return True
    return False


# Get the total count of users
async def get_user_count(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count(User.id))  # SQL COUNT(id)
    )
    return result.scalar() or 0


# Get the count of active users (you may want to modify the logic if there's an 'is_active' column)
async def get_active_user_count(db: AsyncSession) -> int:
    result = await db.execute(select(User).filter(User.is_active == True))
    return result.scalars().count()
