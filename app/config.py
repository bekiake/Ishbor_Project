import os
from pathlib import Path
from dotenv import load_dotenv

# Muhit o'zgaruvchilarini yuklash
load_dotenv()

# Loyiha yo'lini topish (BASE_DIR Django-dagi kabi)
BASE_DIR = Path(__file__).resolve().parent.parent  # Bu 'app/' papkasi bo'ladi

# Xavfsizlik va JWT sozlamalari
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-ch_l$asqwt38h!pp%*yc4b3pdcpz24zkda=i8u!^-la*4)d6+2")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 soat

# Debug sozlamalari
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Ruxsat berilgan hostlar
ALLOWED_HOSTS = ["*"]

# FastAPI uchun API prefix
API_V1_STR = "/api/v1"
PROJECT_NAME = "Ishbor API"

# CORS sozlamalari
BACKEND_CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",  # React frontendi uchun
    "http://localhost:5173",  # Vite frontendi uchun
]

# Ma'lumotlar bazasi sozlamalari
DB_TYPE = os.getenv("DB_TYPE", "sqlite")

if DB_TYPE == "postgresql":
    # PostgreSQL uchun
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "ishbor_db")

    SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    # SQLite uchun (Django dagi kabi)
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{BASE_DIR / 'ishbor.db'}"

# Static fayllar va media fayllar uchun sozlamalar
STATIC_URL = "/static/"
STATIC_DIR = os.path.join(BASE_DIR, "static")
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Upload fayllar uchun sozlamalar
UPLOAD_DIR = os.path.join(MEDIA_ROOT, "uploads")
WORKER_IMAGES_DIR = os.path.join(UPLOAD_DIR, "workers")

# Vaqt mintaqasi sozlamalari
TIMEZONE = "Asia/Tashkent"

# Logging sozlamalari
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": True
        },
        "app": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False
        },
    }
}

# Papkalarni yaratish (media, uploads, va h.k.)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(WORKER_IMAGES_DIR, exist_ok=True)