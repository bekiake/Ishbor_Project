"""
API routing

Barcha API endpointlarini birlashtiruvchi router
"""
from fastapi import APIRouter

from app.api.endpoints import users, workers, feedbacks, auth, utils

# Asosiy API router
api_router = APIRouter()

# User routerini qo'shish
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
)

# Worker routerini qo'shish
api_router.include_router(
    workers.router,
    prefix="/workers",
    tags=["workers"],
)

# Feedback routerini qo'shish
api_router.include_router(
    feedbacks.router,
    prefix="/feedbacks",
    tags=["feedbacks"],
)

# Authentication routerini qo'shish
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"],
)

# Utillar routerini qo'shish
api_router.include_router(
    utils.router,
    prefix="/utils",
    tags=["utilities"],
)