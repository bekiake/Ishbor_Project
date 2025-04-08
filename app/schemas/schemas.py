from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator, field_validator


# User schemas
class UserBase(BaseModel):
    """User uchun asosiy ma'lumotlar"""
    telegram_id: str
    name: Optional[str] = None
    is_worker: bool = False


class UserCreate(UserBase):
    """User yaratish uchun schema"""
    pass


class UserUpdate(BaseModel):
    """User yangilash uchun schema"""
    name: Optional[str] = None


class UserInDBBase(UserBase):
    """Database-da saqlangan User ma'lumotlari"""
    id: int
    created: datetime
    updated: datetime
    is_active: bool = True

    class Config:
        from_attributes = True  # SQLAlchemy modellardan ma'lumotlarni olish uchun


class User(UserInDBBase):
    """User response schema"""
    pass


# Worker schemas
class WorkerBase(BaseModel):
    """Worker uchun asosiy ma'lumotlar"""
    telegram_id: str
    name: Optional[str] = None
    about: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    payment_type: Optional[str] = "barchasi"
    daily_payment: Optional[int] = None
    languages: Optional[str] = None
    skills: Optional[str] = None
    location: Optional[str] = None


class WorkerCreate(WorkerBase):
    """Worker yaratish uchun schema"""
    pass


class WorkerUpdate(BaseModel):
    """Worker yangilash uchun schema"""
    name: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    payment_type: Optional[str] = None
    daily_payment: Optional[int] = None
    languages: Optional[str] = None
    skills: Optional[str] = None
    location: Optional[str] = None


class WorkerLocation(BaseModel):
    """Worker lokatsiyasini yangilash uchun schema"""
    latitude: float
    longitude: float


class WorkerInDBBase(WorkerBase):
    """Database-da saqlangan Worker ma'lumotlari"""
    id: int
    image: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True  # SQLAlchemy modellardan ma'lumotlarni olish uchun



class Worker(WorkerInDBBase):
    """Worker response schema"""
    languages_list: Optional[List[str]] = None
    skills_list: Optional[List[str]] = None
    location_coords: Optional[Dict[str, float]] = None

    # Eski @root_validator o'rniga @model_validator ishlatish
    @field_validator('languages_list', 'skills_list', 'location_coords', mode='before')
    @classmethod
    def set_lists_and_coords(cls, values, info):
        """
        Qo'shimcha ma'lumotlarni qayta ishlash
        """
        data = info.data  # Modelning barcha ma'lumotlari

        # Languages ro'yxatini hosil qilish
        languages = data.get('languages')
        if languages:
            languages_list = [lang.strip() for lang in languages.split(',')]
        else:
            languages_list = []

        # Skills ro'yxatini hosil qilish
        skills = data.get('skills')
        if skills:
            skills_list = [skill.strip() for skill in skills.split(',')]
        else:
            skills_list = []

        # Lokatsiyani qayta ishlash
        location = data.get('location')
        location_coords = None
        if location:
            try:
                lat, lng = map(float, location.split(','))
                location_coords = {'latitude': lat, 'longitude': lng}
            except (ValueError, TypeError):
                pass

        # Field name bo'yicha qiymatni qaytarish
        field_name = info.field_name
        if field_name == 'languages_list':
            return languages_list
        elif field_name == 'skills_list':
            return skills_list
        elif field_name == 'location_coords':
            return location_coords
        return values

class Feedbackss(BaseModel):
    id: Optional[int]  # `id` avtomatik tarzda yaratiladi
    worker_id: int
    user_id: int
    rate: int
    text: str
    create_at: Optional[datetime] = None  # Yaratilish sanasi
    update_at: Optional[datetime] = None  # Yangilanish sanasi
    user_name: Optional[str] = None  # Foydalanuvchi nomi (agar kerak bo'lsa)

    class Config:
        orm_mode = True


# Feedback schemas
class FeedbackBase(BaseModel):
    """Feedback uchun asosiy ma'lumotlar"""
    worker_id: int
    user_name: str
    rate: int = Field(1, ge=1, le=5)
    text: Optional[str] = None


class FeedbackCreate(BaseModel):
    worker_id: int
    rate: int
    text: Optional[str] = None
    

class FeedbackResponse(BaseModel):
    id: int
    text: str
    rating: int

    class Config:
        orm_mode = True
        

class FeedbackUpdate(BaseModel):
    """Feedback yangilash uchun schema"""
    rate: Optional[int] = Field(None, ge=1, le=5)
    text: Optional[str] = None


class FeedbackInDBBase(FeedbackBase):
    """Database-da saqlangan Feedback ma'lumotlari"""
    id: int
    create_at: datetime
    update_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True  # SQLAlchemy modellardan ma'lumotlarni olish uchun


class Feedback(FeedbackInDBBase):
    """Feedback response schema"""
    pass


# Bog'liq response schemalar
class WorkerWithFeedbacks(Worker):
    """Feedbacks bilan birga Worker"""
    feedbacks: List[Feedback] = []


class UserWithFeedbacks(User):
    """Feedbacks bilan birga User"""
    feedbacks: List[Feedback] = []


# Token schemas
class Token(BaseModel):
    """Token response"""
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """Token payload"""
    sub: Optional[str] = None
    exp: Optional[int] = None


# Search schemas
class WorkerSearchParams(BaseModel):
    """Worker qidirish parametrlari"""
    name: Optional[str] = None
    skills: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    payment_type: Optional[str] = None
    gender: Optional[str] = None
    min_payment: Optional[int] = None
    max_payment: Optional[int] = None
    location: Optional[str] = None
    distance: Optional[float] = None  # km hisobida


# Statistics schemas
class WorkerStats(BaseModel):
    """Worker statistikasi"""
    total_workers: int
    active_workers: int
    average_rating: float
    payment_distribution: Dict[str, int]
    gender_distribution: Dict[str, int]


class SystemStats(BaseModel):
    """Tizim statistikasi"""
    total_users: int
    total_workers: int
    total_feedbacks: int
    average_rating: float
    top_skills: List[Dict[str, Any]]
    top_languages: List[Dict[str, Any]]
    
    

class FeedbackOut(BaseModel):
    id: int
    rate: int
    text: Optional[str]
    create_at: datetime
    user_name: Optional[str]  # Bu qo‘shilgan maydon

    class Config:
        orm_mode = True
        

class WorkerDetail(BaseModel):
    id: int
    telegram_id: str
    name: Optional[str]
    image: Optional[str]
    age: Optional[int]
    phone: Optional[str]
    gender: Optional[str]
    payment_type: Optional[str]
    daily_payment: Optional[int]
    languages: Optional[str]
    skills: Optional[str]
    location: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    feedbacks: List[FeedbackResponse]

    class Config:
        orm_mode = True