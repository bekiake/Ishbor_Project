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
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer

from app.api.api import api_router
from app.core.settings import settings
from app.database import Base, engine
from app.core.middleware import LogMiddleware

# FastAPI ilovasini yaratish
app = FastAPI(
    title="Ishbor API",
    version="1.0.0",
    description="Ishbor loyihasi uchun FastAPI backend",
    docs_url="/docs",
    openapi_url="/api/v1/openapi.json"
)

# Jadval yaratish uchun asinxron funksiya
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Startup eventida jadval yaratish
@app.on_event("startup")
async def on_startup():
    await init_db()

def custom_openapi():
    """Custom OpenAPI sxemasi"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}

    openapi_schema["components"]["securitySchemes"]["Bearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter JWT token with 'Bearer' prefix"
    }

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