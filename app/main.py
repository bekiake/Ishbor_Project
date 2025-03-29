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


# 📌 Ma'lumotlar bazasini yaratish
Base.metadata.create_all(bind=engine)

# 📌 FastAPI ilovasini yaratish
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Ishbor loyihasi uchun FastAPI backend",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 📌 OAuth2 Bearer Token uchun konfiguratsiya
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/token")


# 📌 Swagger UI (OpenAPI) uchun autentifikatsiya qo‘shish
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
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token here",
        }
    }

    # 🔹 Barcha endpointlarga "security" qo‘shish
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "security" not in method:
                method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return openapi_schema

app.openapi = custom_openapi


# 📌 CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📌 Logging middleware
app.add_middleware(LogMiddleware)

# 📌 Static va media fayllar uchun mounting
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
app.mount("/media", StaticFiles(directory=settings.MEDIA_ROOT), name="media")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# 📌 API routerlarni qo‘shish (lekin `/token` endpointidan autentifikatsiyani olib tashlash)
app.include_router(api_router, prefix=settings.API_V1_STR)


# 📌 Asosiy sahifa
@app.get("/")
async def root():
    return {
        "app_name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "description": "Ishbor loyihasi uchun FastAPI backend",
        "docs_url": "/docs",
        "api_url": settings.API_V1_STR,
    }


# 📌 Health Check (avtorizatsiyasiz)
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": "production" if not settings.DEBUG else "development",
    }


# 📌 Ishga tushirish
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
