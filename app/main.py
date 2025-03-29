"""
Ishbor loyihasi uchun FastAPI backend
"""

import logging
import time
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles

from app.api.api import api_router
from app.core.settings import settings
from app.database import Base, engine
from app.core.middleware import LogMiddleware
from app.api.endpoints.auth import router as auth_router

# Ma'lumotlar bazasi jadvallarini yaratish
Base.metadata.create_all(bind=engine)

# FastAPI ilovasini yaratish
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Ishbor loyihasi uchun FastAPI backend",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# OAuth2 Bearer Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/token")

# OpenAPI sxemasini faqat Bearer token orqali ishlaydigan qilib o‘zgartirish
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token"
        }
    }
    openapi_schema["security"] = [{"Bearer": []}]
    app.openapi_schema = openapi_schema
    return openapi_schema

app.openapi = custom_openapi

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
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth")

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
        "environment": settings.ENV,
    }

if __name__ == "__main__":
    # Log formatini yaxshilash
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )
    
    # Uvicorn serverni ishga tushirish
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
