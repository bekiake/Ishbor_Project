"""
FastAPI ilovasi

Loyihaning asosiy fayli
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path
import time

from app.api.api import api_router
from app.core.settings import settings
from app.database import Base, engine
from app.core.middleware import LogMiddleware


Base.metadata.create_all(bind=engine)

# FastAPI ilovasini yaratish
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Ishbor loyihasi uchun FastAPI backend",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",  # Shu qatordan xatolik chiqishi mumkin
    docs_url="/docs",
    redoc_url="/redoc",
)

# Bearer token konfiguratsiyasi
app.openapi_components = {
    "securitySchemes": {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token"
        }
    }
}

app.openapi_security = [{"Bearer": []}]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
app.add_middleware(LogMiddleware)

# Static va media fayllar uchun mounting
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
app.mount("/media", StaticFiles(directory=settings.MEDIA_ROOT), name="media")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# API routerlarini qo'shish
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Asosiy sahifa"""
    return {
        "app_name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "description": "Ishbor loyihasi uchun FastAPI backend",
        "docs_url": "/docs",
        "api_url": settings.API_V1_STR,
    }


@app.get("/health")
async def health_check():
    """Health check endpointi"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": "production" if not settings.DEBUG else "development",
    }


if __name__ == "__main__":
    # Agarda to'g'ridan-to'g'ri bu fayl ishga tushirilsa
    log_level = "info" if not settings.DEBUG else "debug"
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=log_level,
    )
