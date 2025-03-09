#!/bin/bash

# Ishbor proyekti uchun FastAPI va Django ni bir vaqtda ishga tushirish skriti

# Virtual muhitni faollashtirish
if [ -d "venv" ]; then
    echo "Virtual muhitni faollashtirish..."
    source venv/bin/activate
else
    echo "Virtual muhit topilmadi. Yangi muhit yaratilmoqda..."
    python -m venv venv
    source venv/bin/activate

    echo "Kerakli paketlar o'rnatilmoqda..."
    pip install -r requirements.txt
fi

# Papkalarni yaratish
mkdir -p staticfiles
mkdir -p media/uploads/workers

# Django migratsiyalarni amalga oshirish
echo "Django migratsiyalarini amalga oshirish..."
python manage.py migrate

# Portlarni tekshirish
function is_port_in_use() {
    if command -v lsof > /dev/null; then
        lsof -i:"$1" > /dev/null
        return $?
    elif command -v netstat > /dev/null; then
        netstat -tuln | grep -q ":$1 "
        return $?
    else
        echo "lsof yoki netstat buyrug'i topilmadi. Portni tekshirib bo'lmaydi."
        return 0
    fi
}

# Django va FastAPI uchun portlar
DJANGO_PORT=8000
FASTAPI_PORT=8001

if is_port_in_use $DJANGO_PORT; then
    echo "OGOHLANTIRISH: $DJANGO_PORT port ishlatilmoqda. Django uchun boshqa port tanlanadi."
    DJANGO_PORT=8002
fi

if is_port_in_use $FASTAPI_PORT; then
    echo "OGOHLANTIRISH: $FASTAPI_PORT port ishlatilmoqda. FastAPI uchun boshqa port tanlanadi."
    FASTAPI_PORT=8003
fi

# Django va FastAPI ni parallel ishga tushirish
echo "Django serverni ishga tushirish... ($DJANGO_PORT portida)"
python manage.py runserver $DJANGO_PORT > django_server.log 2>&1 &
DJANGO_PID=$!

echo "FastAPI serverni ishga tushirish... ($FASTAPI_PORT portida)"
uvicorn app.main:app --reload --port=$FASTAPI_PORT > fastapi_server.log 2>&1 &
FASTAPI_PID=$!

echo ""
echo "===================================================="
echo "Ishbor proyekti ishga tushirildi!"
echo "----------------------------------------------------"
echo "Django admin panel: http://localhost:$DJANGO_PORT/admin/"
echo "FastAPI API: http://localhost:$FASTAPI_PORT/"
echo "FastAPI dokumentatsiya: http://localhost:$FASTAPI_PORT/docs"
echo "===================================================="
echo ""
echo "Loglarni ko'rish uchun:"
echo "  Django: tail -f django_server.log"
echo "  FastAPI: tail -f fastapi_server.log"
echo ""
echo "Serverlarni to'xtatish uchun CTRL+C bosing..."
echo ""

# Foydalanuvchi CTRL+C bosganda serverlarni to'xtatish
trap 'echo "Serverlar to'\''xtatilmoqda..."; kill $DJANGO_PID $FASTAPI_PID; exit' INT

# Asosiy skript serverlar ishlayotganini kutadi
wait