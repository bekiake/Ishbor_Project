from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL konfiguratsiyasini olish
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Lazizbek1")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "baza")

# SQLAlchemy uchun PostgreSQL URL
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# PostgreSQL uchun engine yaratish
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Ulanish mavjudligini tekshirish
    pool_recycle=3600,   # 1 soatdan keyin ulanishlarni yangilash
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Model uchun baza klass
Base = declarative_base()

# Database session dependency (FastAPI endpointlar uchun)
def get_db():
    """
    FastAPI dependency sifatida ishlatiladi. Endpoint funksiyalariga
    ma'lumotlar bazasi sessiyasini taqdim etadi.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
