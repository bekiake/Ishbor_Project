from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# PostgreSQL konfiguratsiyasini olish
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Lazizbek1")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "baza")

# SQLAlchemy uchun PostgreSQL URL (async version)
SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# PostgreSQL uchun async engine yaratish
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,  # SQL so'rovlarini konsolda ko'rsatish
    pool_pre_ping=True,  # Ulanish mavjudligini tekshirish
    pool_recycle=3600,   # 1 soatdan keyin ulanishlarni yangilash
)

# Async Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Model uchun baza klass
Base = declarative_base()

# Database session dependency (FastAPI endpointlar uchun)
async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()