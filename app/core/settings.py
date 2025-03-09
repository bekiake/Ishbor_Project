# app/core/settings.py
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import os
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # API va ilova sozlamalari
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Ishbor API"

    # Loyiha yo'lini topish
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Debug sozlamalari
    DEBUG: bool = True

    # CORS sozlamalari
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # JWT sozlamalari
    SECRET_KEY: str = "django-insecure-ch_l$asqwt38h!pp%*yc4b3pdcpz24zkda=i8u!^-la*4)d6+2"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 soat

    # Database sozlamalari
    DB_TYPE: str = "sqlite"
    DB_USER: Optional[str] = "postgres"
    DB_PASSWORD: Optional[str] = "postgres"
    DB_HOST: Optional[str] = "localhost"
    DB_PORT: Optional[str] = "5432"
    DB_NAME: Optional[str] = "ishbor_db"
    SQLALCHEMY_DATABASE_URL: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        """Database URL ni yaratish"""
        if isinstance(v, str):
            return v

        values = info.data  # Barcha ma'lumotlarni olish
        db_type = values.get("DB_TYPE", "sqlite")

        if db_type == "postgresql":
            return (
                f"postgresql://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}@"
                f"{values.get('DB_HOST')}:{values.get('DB_PORT')}/{values.get('DB_NAME')}"
            )
        else:
            # SQLite (default)
            return f"sqlite:///{values.get('BASE_DIR') / 'ishbor.db'}"

    # Static va media fayllar sozlamalari
    STATIC_URL: str = "/static/"
    STATIC_DIR: Path = BASE_DIR / "static"
    STATIC_ROOT: Path = BASE_DIR / "staticfiles"

    MEDIA_URL: str = "/media/"
    MEDIA_ROOT: Path = BASE_DIR / "media"

    # Upload fayllar sozlamalari
    UPLOAD_DIR: Path = MEDIA_ROOT / "uploads"
    WORKER_IMAGES_DIR: Path = UPLOAD_DIR / "workers"

    # Fayl yuklash sozlamalari
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif"]

    # Vaqt mintaqasi
    TIMEZONE: str = "Asia/Tashkent"

    # Ruxsat berilgan hostlar
    ALLOWED_HOSTS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"


# Settings klassidan ekzempliar yaratish
settings = Settings()