from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import SQLALCHEMY_DATABASE_URL

# Ma'lumotlar bazasiga ulanish
# SQLite uchun "check_same_thread" parametri kerak
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Engine yaratish
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connect_args,
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