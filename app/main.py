import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import time
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer

from app.api.api import api_router
from app.core.settings import settings
from app.database import Base, engine
from app.core.middleware import LogMiddleware

# Ma'lumotlar bazasini yaratish
Base.metadata.create_all(bind=engine)

# OAuth2 Bearer Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/token")

# FastAPI ilovasini yaratish
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Ishbor loyihasi uchun FastAPI backend",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",  # OpenAPI Swagger UI yoqiladi
    redoc_url="/redoc",  # ReDoc hujjatlar ham bo‘lishi mumkin
)


# OpenAPI sxemasini faqat Bearer token orqali ishlaydigan qilib sozlash
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

# API routerlarini qo'shish va authentication endpointlaridan tashqari barcha endpointlarga autentifikatsiyani majburiy qilish
app.include_router(api_router, prefix=settings.API_V1_STR, dependencies=[Depends(oauth2_scheme)], include_in_schema=False)

@app.get("/")
async def root(token: str = Depends(oauth2_scheme)):
    """Asosiy sahifa"""
    return {
        "app_name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "description": "Ishbor loyihasi uchun FastAPI backend",
        "docs_url": settings.API_V1_STR + "/docs",
        "api_url": settings.API_V1_STR,
    }

@app.get("/health")
async def health_check(token: str = Depends(oauth2_scheme)):
    """Health check endpointi"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": "production" if not settings.DEBUG else "development",
    }

if __name__ == "__main__":
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
