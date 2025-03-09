import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Logger yaratish
logger = logging.getLogger("app.middleware")


class LogMiddleware(BaseHTTPMiddleware):
    """
    So'rovlarni qayd qilish uchun middleware

    Har bir so'rov va uning bajarilish vaqtini logga yozadi
    """

    async def dispatch(self, request: Request, call_next):
        """
        So'rovni qayta ishlash va logga yozish
        """
        start_time = time.time()

        # Client IP manzilini aniqlash
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # So'rov boshlanishi logga yozish
        logger.info(
            f"Start request: {request.method} {request.url.path} from {client_ip}"
        )

        try:
            # So'rovni keyingi middlewarelar orqali o'tkazish
            response = await call_next(request)

            # So'rov yakunlangandan keyin logga yozish
            process_time = time.time() - start_time
            logger.info(
                f"Complete request: {request.method} {request.url.path} "
                f"from {client_ip} - Status: {response.status_code} - "
                f"Took: {process_time:.4f}s"
            )

            # Response headeriga bajarilish vaqtini qo'shish
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            # Xatolik yuz berganda logga yozish
            process_time = time.time() - start_time
            logger.error(
                f"Error in request: {request.method} {request.url.path} "
                f"from {client_ip} - Error: {str(e)} - "
                f"Took: {process_time:.4f}s"
            )
            raise


def setup_cors(app):
    """
    CORS sozlamalari

    CORS middlewareini sozlash uchun yordamchi funksiya
    """
    from fastapi.middleware.cors import CORSMiddleware
    from app.core.settings import Settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=Settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )