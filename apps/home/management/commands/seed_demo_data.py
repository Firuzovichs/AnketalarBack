"""
python manage.py seed_demo_data

10 ta test foydalanuvchi (5 erkak + 5 ayol),
3 ta banner, 3 ta yangilik yaratadi.
"""
import io
import random
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

from apps.users.models import User, UserProfile, UserPhoto, Interest
from apps.locations.models import District
from apps.home.models import Banner, News

# Demo userlar shu nuqta atrofida tasodifiy sochiladi — shunda ular
# "Qidirish" xaritasida (standart 10 km radius) pin sifatida ko'rinadi.
# (Eslatma: avval lat/lng umuman berilmagani uchun MapSearchView ularni
# "profile__latitude__isnull=True" filtri bilan chiqarib tashlayotgan edi —
# like/match bo'lganlar chiqarilmasa ham, koordinatasi yo'qlar hech qachon
# pin bo'lib chiqmaydi.)
TASHKENT_LAT = 41.311081
TASHKENT_LNG = 69.240562


def random_nearby_point(center_lat: float, center_lng: float, max_km: float = 4.0):
    """Markazdan tasodifiy nuqta qaytaradi — demo userlar bir joyga
    to'planib qolmasligi uchun (~max_km radius ichida, tabiiy sochilgan)."""
    lat_offset = random.uniform(-max_km, max_km) / 111.0
    lng_offset = random.uniform(-max_km, max_km) / (111.0 * 0.75)  # ~41° kenglikdagi tuzatish
    lat = round(center_lat + lat_offset, 6)
    lng = round(center_lng + lng_offset, 6)
    return Decimal(str(lat)), Decimal(str(lng))


# ── Rang palitralari ─────────────────────────────────────────────────
MALE_COLORS   = ["#4A90D9", "#5B6AF0", "#2ECC71", "#E74C3C", "#9B59B6"]
FEMALE_COLORS = ["#FF6B9D", "#FF9A8B", "#F093FB", "#FCCB90", "#D57EEB"]

MALES = [
    ("Jasur",    "Toshmatov",  25, "1999-03-15"),
    ("Bobur",    "Karimov",    28, "1996-07-22"),
    ("Sanjar",   "Yusupov",    24, "2000-01-10"),
    ("Dilshod",  "Nazarov",    30, "1994-11-05"),
    ("Ulugbek",  "Rahimov",    27, "1997-05-30"),
]
FEMALES = [
    ("Malika",   "Abdullayeva", 23, "2001-04-18"),
    ("Nilufar",  "Hasanova",   26, "1998-09-12"),
    ("Zulfiya",  "Mirzayeva",  24, "2000-06-25"),
    ("Munira",   "Qodirova",   29, "1995-02-08"),
    ("Shahnoza", "Ergasheva",  25, "1999-12-01"),
]

BANNERS = [
    ("Anketalar Premium",   "Premium a'zolik bilan cheksiz imkoniyatlar!",   "#FF6B9D", "#C44FED"),
    ("Yangi tanishuvlar",   "Bugun yangi odamlar bilan tanishing 🌟",         "#4A90D9", "#5B6AF0"),
    ("VIP obuna",           "VIP foydalanuvchilar ko'proq match oladi 👑",    "#F7971E", "#FFD200"),
]

NEWS = [
    (
        "Anketalar 2.0 yangilandi!",
        "Ilovamizning yangi versiyasida juda ko'p yaxshi o'zgarishlar bo'ldi.",
        "Yangi versiyada tezkor qidiruv, yaxshilangan tavsiya tizimi va ko'plab boshqa qiziqarli xususiyatlar qo'shildi. Foydalanuvchilarimiz uchun eng yaxshi tajribani yaratishga harakat qilmoqdamiz.",
        "#4A90D9", "#7B68EE",
    ),
    (
        "Xavfsiz tanishuv bo'yicha maslahatlar",
        "Onlayn tanishuvda o'zingizni xavfsiz saqlash uchun 5 ta muhim maslahat.",
        "1. Shaxsiy ma'lumotlaringizni darhol ulashmang. 2. Video qo'ng'iroqdan foydalaning. 3. Birinchi uchrashuv uchun jamoat joyini tanlang. 4. Ishonchli odamga xabar bering. 5. Instinktingizga ishoning.",
        "#2ECC71", "#1ABC9C",
    ),
    (
        "Muvaffaqiyatli juftliklar haqida",
        "Anketalar orqali topishgan juftliklarning ilhomlantiruvchi hikoyalari.",
        "Har kuni yuzlab odamlar Anketalar orqali o'z yaqin insonlarini topmoqda. Ularning hikoyalari bizni ilhomlantirib, yanada yaxshiroq xizmat ko'rsatishga undaydi.",
        "#FF6B9D", "#FF8E53",
    ),
]


def make_gradient_image(width: int, height: int, color1: str, color2: str, label: str = "") -> bytes:
    """Gradient rangli rasm yaratadi (JPEG)."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
    r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

    for x in range(width):
        t = x / width
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        draw.line([(x, 0), (x, height)], fill=(r, g, b))

    # Matn
    if label:
        try:
            draw.text((width // 2 - len(label) * 4, height // 2 - 10),
                      label, fill=(255, 255, 255))
        except Exception:
            pass

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def make_avatar(width: int, height: int, color: str, initials: str) -> bytes:
    """Boshlang'ich harf(lar)li avatar yaratadi."""
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    # Daire
    draw.ellipse([0, 0, width - 1, height - 1],
                 fill=color)
    # Matn
    try:
        draw.text((width // 2 - len(initials) * 8, height // 2 - 12),
                  initials, fill=(255, 255, 255))
    except Exception:
        pass

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


class Command(BaseCommand):
    help = "Demo ma'lumotlar: 10 user + bannerlar + yangiliklar"

    def handle(self, *args, **options):
        self._seed_users()
        self._seed_banners()
        self._seed_news()

    # ── Users ────────────────────────────────────────────────────────
    def _seed_users(self):
        interests = list(Interest.objects.all()[:5])
        districts = list(District.objects.select_related('region').all()[:10])

        created = 0
        all_users = [("M", MALES, MALE_COLORS), ("F", FEMALES, FEMALE_COLORS)]

        for gender, persons, colors in all_users:
            for i, (first, last, age, bdate) in enumerate(persons):
                email = f"{first.lower()}.{last.lower()}@demo.uz"
                lat, lng = random_nearby_point(TASHKENT_LAT, TASHKENT_LNG)

                existing = User.objects.filter(email=email).first()
                if existing:
                    # Allaqachon mavjud — lekin avvalroq lat/lng berilmagan
                    # bo'lishi mumkin (eski xato), shuning uchun bu yerda
                    # to'ldirib qo'yamiz, shunda xaritada ko'rina boshlaydi.
                    profile = getattr(existing, 'profile', None)
                    if profile and (profile.latitude is None or profile.longitude is None):
                        profile.latitude = lat
                        profile.longitude = lng
                        profile.save(update_fields=['latitude', 'longitude'])
                        self.stdout.write(f"  📍 {email} uchun joylashuv to'ldirildi")
                    else:
                        self.stdout.write(f"  ⏭  {email} allaqachon mavjud")
                    continue

                user = User.objects.create_user(
                    email=email,
                    password="Demo1234!",
                    is_active=True,
                )

                district = districts[i % len(districts)] if districts else None

                profile = UserProfile.objects.create(
                    user=user,
                    first_name=first,
                    last_name=last,
                    birth_date=date.fromisoformat(bdate),
                    gender=gender,
                    height=random.randint(160, 185) if gender == "M" else random.randint(155, 172),
                    weight=random.randint(65, 85)   if gender == "M" else random.randint(48, 68),
                    is_face_verified=True,
                    district=district,
                    latitude=lat,
                    longitude=lng,
                )
                if interests:
                    profile.interests.set(random.sample(interests, min(3, len(interests))))

                # Avatar rasm
                color = colors[i % len(colors)]
                img_bytes = make_avatar(400, 400, color, first[0] + last[0])
                photo = UserPhoto(user=user, is_main=True, order=0)
                photo.image.save(
                    f"demo_{first.lower()}_{last.lower()}.jpg",
                    ContentFile(img_bytes), save=True
                )

                created += 1
                icon = "👨" if gender == "M" else "👩"
                self.stdout.write(f"  {icon} {first} {last} ({email}) yaratildi")

        self.stdout.write(self.style.SUCCESS(f"\n✅ {created} yangi foydalanuvchi qo'shildi"))

    # ── Banners ──────────────────────────────────────────────────────
    def _seed_banners(self):
        if Banner.objects.exists():
            self.stdout.write("  ⏭  Bannerlar allaqachon mavjud")
            return

        for i, (title, desc, c1, c2) in enumerate(BANNERS):
            img_bytes = make_gradient_image(800, 400, c1, c2, title)
            banner = Banner(
                title=title, description=desc,
                is_active=True, order=i,
            )
            banner.image.save(
                f"banner_{i+1}.jpg",
                ContentFile(img_bytes), save=True
            )
            self.stdout.write(f"  🖼  Banner: {title}")

        self.stdout.write(self.style.SUCCESS(f"✅ {len(BANNERS)} banner yaratildi"))

    # ── News ─────────────────────────────────────────────────────────
    def _seed_news(self):
        if News.objects.exists():
            self.stdout.write("  ⏭  Yangiliklar allaqachon mavjud")
            return

        for i, (title, desc, content, c1, c2) in enumerate(NEWS):
            img_bytes = make_gradient_image(800, 450, c1, c2, "")
            news = News(
                title=title, description=desc, content=content,
                is_active=True,
            )
            news.image.save(
                f"news_{i+1}.jpg",
                ContentFile(img_bytes), save=True
            )
            self.stdout.write(f"  📰  Yangilik: {title}")

        self.stdout.write(self.style.SUCCESS(f"✅ {len(NEWS)} yangilik yaratildi"))
