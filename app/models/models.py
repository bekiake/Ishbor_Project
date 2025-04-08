from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime

from app.database import Base


class User(Base):

    __tablename__ = "workers_user"  # Django jadval nomi

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(100), unique=True, index=True)
    is_worker = Column(Boolean, default=False)
    name = Column(String(255), nullable=True)
    created = Column(DateTime, default=func.now())
    updated = Column(DateTime, default=func.now(), onupdate=func.now())

    # Django modelida foreign key qanday nomlangan bo'lsa, relationship ham shunga mos bo'lishi kerak
    feedbacks = relationship("Feedback", back_populates="user")

    def __str__(self):
        return self.name or self.telegram_id


class Worker(Base):

    __tablename__ = "workers_worker"  # Django jadval nomi

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(100), unique=True, index=True)
    name = Column(String(255), nullable=True)
    image = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    phone = Column(String(255), nullable=True, unique=True)
    gender = Column(String(255), nullable=True)
    payment_type = Column(String(255), nullable=True, default="barchasi")
    daily_payment = Column(Integer, nullable=True)
    languages = Column(String(255), nullable=True)
    skills = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Django modelida foreign key qanday nomlangan bo'lsa, relationship ham shunga mos bo'lishi kerak
    feedbacks = relationship("Feedback", back_populates="worker")

    
    def get_languages_list(self):
        """
        Tillarni ro'yxat sifatida qaytaradi
        """
        if not self.languages:
            return []
        return [lang.strip() for lang in self.languages.split(",")]

    def set_languages(self, languages_list):
        """
        Tillarni ro'yxatdan string sifatida o'rnatadi
        """
        if languages_list:
            self.languages = ", ".join(languages_list)
        else:
            self.languages = None

    def get_skills_list(self):
        """
        Ko'nikmalarni ro'yxat sifatida qaytaradi
        """
        if not self.skills:
            return []
        return [skill.strip() for skill in self.skills.split(",")]

    def set_skills(self, skills_list):
        """
        Ko'nikmalarni ro'yxatdan string sifatida o'rnatadi
        """
        if skills_list:
            self.skills = ", ".join(skills_list)
        else:
            self.skills = None

    def __str__(self):
        return self.name or self.telegram_id


class Feedback(Base):
    __tablename__ = "workers_feedback"  # Django jadval nomi

    id = Column(Integer, primary_key=True, index=True)
    # Foreign key nomlarini Django kabi nomlang
    worker_id = Column(Integer, ForeignKey("workers_worker.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("workers_user.id", ondelete="CASCADE"))
    rate = Column(Integer, default=1)
    text = Column(Text, nullable=True)
    create_at = Column(DateTime, default=func.now())
    update_at = Column(DateTime, default=func.now(), onupdate=func.now())

    worker = relationship("Worker", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")

    def __str__(self):
        return f"{self.worker.name} - {self.user.name} - {self.rate}"

class Skills(Base):
    __tablename__ = "workers_skills"  # Django jadval nomi

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True, unique=True)