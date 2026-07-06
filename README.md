# Anketalar — Backend

Python 3.11 + Django 4.2 + Django REST Framework

## Tuzilma

```
backend/
├── config/
│   ├── settings/       base / development / production
│   ├── urls.py         barcha API marshrutlar
│   ├── asgi.py         WebSocket (Channels)
│   └── celery.py       Async tasks
├── apps/
│   ├── users/          Auth, Profil, Rasm, Yuz skaneri
│   ├── locations/      Davlat → Viloyat → Tuman
│   ├── matches/        Like / Accept / Reject / Match
│   ├── stories/        Story CRUD, Ko'ruvchilar, Stikerlar
│   ├── chat/           ChatRoom, Message (WebSocket)
│   ├── notifications/  Bildirishnomalar (Celery + FCM)
│   ├── subscriptions/  Oddiy / Premium / VIP rejalari
│   └── search/         Qidiruv + Filterlar + Radius
└── utils/
    ├── pagination.py
    ├── permissions.py
    └── helpers.py      OTP, Yosh hisoblash, Haversine
```

## API Endpointlar

### Auth (`/api/auth/`)
| Method | URL | Tavsif |
|--------|-----|--------|
| POST | `/send-otp/` | OTP yuborish (email/telefon) |
| POST | `/verify-otp/` | OTP tasdiqlash |
| POST | `/register/` | Ro'yxatdan o'tish |
| POST | `/login/` | Kirish |
| POST | `/token/refresh/` | Tokenni yangilash |
| POST | `/logout/` | Chiqish |
| GET/PATCH | `/me/` | Mening profilim |
| POST | `/profile/setup/` | Profil to'ldirish |
| POST | `/profile/face-scan/` | Yuz skaneri yuklash |
| GET/POST | `/photos/` | Rasmlar |
| DELETE | `/photos/<id>/` | Rasm o'chirish |
| GET | `/interests/` | Qiziqishlar ro'yxati |
| GET | `/goals/` | Maqsadlar ro'yxati |

### Locations (`/api/locations/`)
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/countries/` | Davlatlar |
| GET | `/regions/?country=<id>` | Viloyatlar |
| GET | `/districts/?region=<id>` | Tumanlar |

### Matches (`/api/matches/`)
| Method | URL | Tavsif |
|--------|-----|--------|
| POST | `/like/` | Like tashlash |
| POST | `/like/<id>/respond/` | Qabul/Rad qilish |
| GET | `/received/` | Kelgan likelar (Premium+) |
| GET | `/` | Matchlar ro'yxati |

### Stories (`/api/stories/`)
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/feed/` | Match bo'lganlarning storylari |
| POST | `/` | Story qo'shish |
| GET | `/mine/` | Mening storylarim |
| GET/DELETE | `/<id>/` | Story detail/o'chirish |
| GET | `/<id>/viewers/` | Kim ko'rganlar (egasi uchun) |
| GET | `/<id>/reactions/` | Reaksiyalar (egasi uchun) |
| POST | `/<id>/react/` | Stiker bosish |

### Chat (`/api/chat/`)
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/rooms/` | Chat xonalar ro'yxati |
| GET | `/rooms/<id>/` | Xona detail |
| GET | `/rooms/<id>/messages/` | Xabarlar |
| POST | `/rooms/<id>/messages/send/` | Xabar yuborish |
| DELETE | `/messages/<id>/delete/` | Xabar o'chirish |

**WebSocket:** `ws://host/ws/chat/<room_id>/?token=<access_token>`

WebSocket events:
```json
// Xabar yuborish
{"action": "send_message", "message_type": "text", "content": "Salom!"}
// Reply bilan
{"action": "send_message", "message_type": "text", "content": "Javob", "reply_to_id": 5}
// Yozmoqda
{"action": "typing", "is_typing": true}
// O'qildi
{"action": "read", "message_id": 12}
```

### Notifications (`/api/notifications/`)
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/` | Bildirishnomalar |
| GET | `/unread-count/` | O'qilmagan soni |
| POST | `/mark-all-read/` | Hammasini o'qildi |
| POST | `/<id>/mark-read/` | Bittasini o'qildi |

### Search (`/api/search/`)
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/` | Qidiruv (filterlar bilan) |
| GET | `/single/` | Bitta kandidat (Tinder-style) |

**Qidiruv parametrlari:**
`min_age`, `max_age`, `min_height`, `max_height`, `min_weight`, `max_weight`,
`interests=1,2,3`, `goals=1,2`, `district_id`, `radius_km` (Premium+)

### Subscriptions (`/api/subscriptions/`)
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/plans/` | Barcha rejallar |
| GET | `/mine/` | Mening rejam |

## Ishga tushirish

```bash
# 1. Virtual muhit
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. .env fayl
cp .env.example .env

# 3. Migratsiyalar
python manage.py migrate

# 4. Boshlang'ich ma'lumotlar
python manage.py seed_plans
python manage.py seed_interests

# 5. Superuser
python manage.py createsuperuser

# 6. Server (HTTP + WebSocket)
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Yoki Docker bilan
docker-compose up --build
```

## API Docs
`http://localhost:8000/api/docs/` — Swagger UI
