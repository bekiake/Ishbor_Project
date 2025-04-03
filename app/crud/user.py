from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import User
from app.schemas.schemas import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> Optional[User]:

    return db.query(User).filter(User.id == user_id).first()


def get_user_by_telegram_id(db: Session, telegram_id: str) -> Optional[User]:

    return db.query(User).filter(User.telegram_id == telegram_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:

    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:

    db_user = User(
        telegram_id=user.telegram_id,
        name=user.name,
        is_worker=user.is_worker,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:

    db_user = get_user(db, user_id)
    if db_user:
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        db.commit()
        db.refresh(db_user)
    return db_user


def update_user_by_telegram_id(
        db: Session,
        telegram_id: str,
        user_update: UserUpdate
) -> Optional[User]:

    db_user = get_user_by_telegram_id(db, telegram_id)
    if db_user:
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        db.commit()
        db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:

    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False


def get_user_count(db: Session) -> int:

    return db.query(User).count()


def get_active_user_count(db: Session) -> int:

    return db.query(User).count()