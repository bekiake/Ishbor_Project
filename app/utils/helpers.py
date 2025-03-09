import os
import shutil
from fastapi import UploadFile
from typing import Optional
import uuid
from pathlib import Path


def save_upload_file(upload_file: UploadFile, destination: str, file_prefix: str = "") -> str:
    """
    Upload qilingan faylni saqlash

    Args:
        upload_file: FastAPI UploadFile obyekti
        destination: Fayl saqlanadigan papka
        file_prefix: Fayl nomiga qo'shiladigan prefix

    Returns:
        Saqlangan fayl nomi (Django modelda saqlanishi uchun)
    """
    # Papkani tekshirish va yaratish
    os.makedirs(destination, exist_ok=True)

    # Fayl nomi generatsiya qilish (xavfsizlik uchun)
    filename = upload_file.filename
    extension = Path(filename).suffix
    safe_filename = f"{file_prefix}{uuid.uuid4().hex}{extension}"

    # To'liq yo'l
    file_path = os.path.join(destination, safe_filename)

    # Faylni saqlash
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    # Django model uchun relative path qaytarish
    django_path = os.path.join("uploads/workers", safe_filename)

    return django_path


def get_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Ikki nuqta orasidagi masofani hisoblash (Haversine formula)

    Args:
        lat1: Birinchi nuqta kenglik
        lon1: Birinchi nuqta uzunlik
        lat2: Ikkinchi nuqta kenglik
        lon2: Ikkinchi nuqta uzunlik

    Returns:
        Masofa (kilometrda)
    """
    import math

    # Yer radiusi (km)
    R = 6371.0

    # Radianga o'tkazish
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Kenglik va uzunlik farqlari
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance