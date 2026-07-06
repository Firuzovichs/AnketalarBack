#!/bin/sh
set -e

echo "⏳ Migratsiyalar..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "🌱 Boshlang'ich ma'lumotlar..."
python manage.py seed_plans
python manage.py seed_interests
python manage.py seed_locations
python manage.py seed_demo_data

echo "📦 Static fayllar..."
python manage.py collectstatic --noinput

echo "🚀 Server ishga tushmoqda..."
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
