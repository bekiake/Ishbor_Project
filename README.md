# Ishbor_Project

Ishchilar va ish beruvchilar uchun platforma

## Loyiha haqida

Bu loyiha FastAPI va Django integratsiyasi orqali ishlab chiqilgan. Django modellarini FastAPI orqali API sifatida taqdim etadi.

## O'rnatish va ishga tushirish

1. Kerakli paketlarni o'rnatish:
```bash
pip install -r requirements.txt
```

2. Djangoni migratsiya qilish:
```bash
cd Ishbor_Project
python manage.py migrate
```

3. FastAPI serverini ishga tushirish:
```bash
cd ..
uvicorn app.main:app --reload
```

4. Brauzerda API dokumentatsiyasini ko'rish:
```
http://localhost:8000/docs
```

## API Endpointlari

### Foydalanuvchilar

- `GET /api/v1/users/` - Barcha foydalanuvchilarni olish
- `POST /api/v1/users/` - Yangi foydalanuvchi yaratish
- `GET /api/v1/users/{user_id}` - ID bo'yicha foydalanuvchini olish
- `PUT /api/v1/users/{user_id}` - Foydalanuvchi ma'lumotlarini yangilash
- `DELETE /api/v1/users/{user_id}` - Foydalanuvchini o'chirish

### Ishchilar

- `GET /api/v1/workers/` - Barcha ishchilarni olish va filtrlash
- `POST /api/v1/workers/` - Yangi ishchi yaratish
- `GET /api/v1/workers/{worker_id}` - ID bo'yicha ishchini olish
- `PUT /api/v1/workers/{worker_id}` - Ishchi ma'lumotlarini yangilash
- `DELETE /api/v1/workers/{worker_id}` - Ishchini o'chirish
- `POST /api/v1/workers/{worker_id}/location` - Ishchi joylashuvini o'rnatish

### Fikrlar

- `GET /api/v1/feedbacks/` - Barcha fikrlarni olish
- `POST /api/v1/feedbacks/` - Yangi fikr yaratish
- `GET /api/v1/feedbacks/{feedback_id}` - ID bo'yicha fikrni olish
- `PUT /api/v1/feedbacks/{feedback_id}` - Fikr ma'lumotlarini yangilash
- `DELETE /api/v1/feedbacks/{feedback_id}` - Fikrni o'chirish
- `GET /api/v1/feedbacks/worker/{worker_id}` - Ishchi haqidagi barcha fikrlarni olish