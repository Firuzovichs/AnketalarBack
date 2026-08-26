"""
python manage.py seed_demo_data

100 ta test foydalanuvchi, 3 ta banner va 3 ta yangilik yaratadi.
"""
import io
import random
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw

from apps.users.models import User, UserProfile, UserPhoto, Interest, Goal
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


MALE_NAMES = [
    "Jasur", "Bobur", "Sanjar", "Dilshod", "Ulugbek", "Alisher", "Rustam", "Bekzod",
    "Shavkat", "Sardor", "Farrux", "Yusuf", "Iskandar", "Nodir", "Nodirbek", "Azamat",
    "Samar", "Islom", "Muhammad", "Javohir", "Akmal", "Sardorbek", "Zokir", "Nuri",
    "Bekhruz", "Odil", "Ibrohim", "Sulton", "Mirjalol", "Farhod", "Fayzullo", "Mansur",
    "Daler", "Asror", "Shavkatbek", "Davron", "Behruz", "Komil", "Anvar", "Ulugbek",
    "Rustambek", "Temurbek", "Rashid", "Barkamol", "Nurbek", "Firdavs", "Samandar",
]

FEMALE_NAMES = [
    "Malika", "Nilufar", "Zulfiya", "Munira", "Shahnoza", "Gulnora", "Madina", "Aziza",
    "Sitora", "Dilnoza", "Sevara", "Farzona", "Nigora", "Baxmal", "Lola", "Malika",
    "Nodira", "Samar", "Asal", "Gulbahor", "Shahlo", "Dilshoda", "Shirin", "Sardoriy",
    "Malayka", "Mavluda", "Gulchehra", "Seydoua", "Nodira", "Muqaddas", "Laziza",
    "Shabnam", "Zarina", "Mubina", "Shaxlo", "Laziz", "Nodira", "Oysha", "Jamila",
]

LAST_NAMES = [
    "Toshmatov", "Karimov", "Yusupov", "Nazarov", "Rahimov", "Mirzo", "Abdullayev",
    "Hasanova", "Qodirova", "Ergasheva", "Ibragimov", "Sodikov", "Rasulov", "Muminov",
    "Soliyev", "Tursunov", "Nuraliev", "Azimov", "Qosimov", "Muminov", "Aliyev", "Qayum",
    "Rashidov", "Shamsiev", "Toshpulatov", "Temirov", "Islomov", "Kadirov", "Nazarbekov",
]

TOTAL_DEMO_USERS = 100
MIN_AGE = 20
MAX_AGE = 43
PHONE_TEMPLATES = ["901", "907", "909", "910", "911", "912", "913", "914", "915", "916"]
PROFILE_ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "demo_profiles"

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


def random_birth_date(min_age: int = MIN_AGE, max_age: int = MAX_AGE) -> date:
    """Tasodifiy tug‘ilgan kun — profil uchun real ko‘rinishdagi yosh uchun."""
    age = random.randint(min_age, max_age)
    day = random.randint(1, 28)
    month = random.randint(1, 12)
    year = date.today().year - age
    return date(year, month, day)


def make_phone(index: int, gender: str) -> str:
    """Demo foydalanuvchi uchun noyob mobil raqam yaratish."""
    operator = PHONE_TEMPLATES[index % len(PHONE_TEMPLATES)]
    rest = f"{index:06d}"
    return f"+998 {operator} {rest[:2]} {rest[2:4]} {rest[4:]}" if gender == "M" else f"+998 {operator} {rest[:3]} {rest[3:5]} {rest[5:]}"


def build_demo_bio(first: str, gender: str) -> str:
    """Kichik, ammo turli biografiya matnlari."""
    if gender == "M":
        intro = [
            f"Salom, men {first}, yoshligimdan hayotdan zavqlanadigan odamman.",
            f"Men {first}man — faollikni, samimiy suhbatni va sifatli vaqtni qadrlayman.",
            f"Yangi do‘stlar va to‘g‘ri tanishuvlar bilan tanishishni yaxshi ko‘raman.",
        ]
    else:
        intro = [
            f"Salom, men {first}. Ochiq, do‘stona va samimiy insonman.",
            f"Mening isming {first}. Oila va do‘stlik qadriyati yuqori turadi.",
            f"{first}man, hayotdagi kichik quvonchlardan zavq olishni yoqtiraman.",
        ]
    base = random.choice(intro)
    extras = [
        "Kino, musiqa va sayohat juda yoqadi.",
        "Kitob o‘qish va sport bilan shug‘ullanishni yaxshi ko‘raman.",
        "Kelajakni birga rejalashtira oladigan samimiy insonni izlayapman.",
        "Sohibjamol suhbatlar, yurish va yangi joylar meni qiynamaydi.",
        "Hayotiy qadriyatlarim: hurmat, ishonch va aniq niyat.",
    ]
    return f"{base} {random.choice(extras)}"


def sync_natural_profile_photo(user, gender: str, profile_index: int) -> None:
    """Demo profilga jinsiga mos, tabiiy portretni asosiy rasm qilib ulaydi.

    Assetlar repozitoriyada saqlanadi, shuning uchun Docker qayta qurilganda ham
    seed bir xil sifatli rasmlarni tiklay oladi. Eski gradient/harfli demo
    rasmlar o'chirilmaydi, faqat soft-delete qilinadi.
    """
    gender_dir = "men" if gender == "M" else "women"
    asset_number = profile_index % 50 + 1
    asset_path = PROFILE_ASSETS_DIR / gender_dir / f"{asset_number:02d}.jpg"
    if not asset_path.exists():
        raise FileNotFoundError(f"Demo profil rasmi topilmadi: {asset_path}")

    filename = f"demo_natural_{gender.lower()}_{asset_number:02d}.jpg"
    active_photos = UserPhoto.objects.filter(user=user, is_deleted=False)
    natural_photo = active_photos.filter(image__endswith=filename).first()

    # Faqat demo profilning yangi tabiiy rasmi faol qoladi. Oldingi placeholder
    # fayllar tarix uchun bazada saqlanadi, ammo API ularni qaytarmaydi.
    active_photos.exclude(pk=getattr(natural_photo, "pk", None)).update(
        is_deleted=True,
        is_main=False,
    )

    if natural_photo is None:
        natural_photo = UserPhoto(user=user, is_main=True, order=0)
        natural_photo.image.save(
            filename,
            ContentFile(asset_path.read_bytes()),
            save=False,
        )
        natural_photo.save()
    elif not natural_photo.is_main or natural_photo.order != 0:
        natural_photo.is_main = True
        natural_photo.order = 0
        natural_photo.save(update_fields=["is_main", "order"])


def sync_profile_fields(profile: UserProfile, data: dict) -> None:
    changed = False
    for field, value in data.items():
        if getattr(profile, field) != value:
            setattr(profile, field, value)
            changed = True
    if changed:
        profile.save(update_fields=list(data.keys()))


class Command(BaseCommand):
    help = "Demo ma'lumotlar: 100 user + bannerlar + yangiliklar"

    def handle(self, *args, **options):
        self._seed_users()
        self._seed_banners()
        self._seed_news()

    # ── Users ────────────────────────────────────────────────────────
    def _seed_users(self):
        interests = list(Interest.objects.all())
        goals = list(Goal.objects.all())
        districts = list(District.objects.select_related('region').all()[:10])
        total_created = 0
        total_existing = 0

        for i in range(TOTAL_DEMO_USERS):
            gender = "M" if i < TOTAL_DEMO_USERS // 2 else "F"
            pool = MALE_NAMES if gender == "M" else FEMALE_NAMES
            first = pool[i % len(pool)]
            last = LAST_NAMES[i % len(LAST_NAMES)]
            lat, lng = random_nearby_point(TASHKENT_LAT, TASHKENT_LNG, max_km=8.0)
            email = f"demo_{gender.lower()}_{i + 1:03d}@demo.uz"
            phone = make_phone(i + 1, gender)

            existing = User.objects.filter(email=email).first()
            bday = random_birth_date()

            if existing:
                profile = getattr(existing, "profile", None)
                if not profile:
                    profile = UserProfile.objects.create(
                        user=existing,
                        first_name=first,
                        last_name=last,
                        birth_date=bday,
                        gender=gender,
                        is_face_verified=True,
                    )
                district = districts[i % len(districts)] if districts else None
                sync_profile_fields(
                    profile,
                    {
                        "first_name": first,
                        "last_name": last,
                        "birth_date": bday,
                        "gender": gender,
                        "height": random.randint(160, 188) if gender == "M" else random.randint(152, 172),
                        "weight": random.randint(55, 95) if gender == "M" else random.randint(45, 78),
                        "bio": build_demo_bio(first, gender),
                        "is_face_verified": True,
                        "district": district,
                        "latitude": lat,
                        "longitude": lng,
                    },
                )
                if not existing.phone:
                    existing.phone = phone
                    existing.save(update_fields=["phone"])
                if interests:
                    profile.interests.set(random.sample(interests, min(4, len(interests))))
                if goals:
                    profile.goals.set(random.sample(goals, min(2, len(goals))))
                sync_natural_profile_photo(existing, gender, i if gender == "M" else i - 50)
                total_existing += 1
                self.stdout.write(f"  ♻️  {first} {last} ({email}) yangilandi")
                continue

            user = User.objects.create_user(
                email=email,
                password="Demo1234!",
                is_active=True,
                phone=phone,
            )

            district = districts[i % len(districts)] if districts else None

            profile = UserProfile.objects.create(
                user=user,
                first_name=first,
                last_name=last,
                birth_date=bday,
                gender=gender,
                height=random.randint(160, 188) if gender == "M" else random.randint(152, 172),
                weight=random.randint(55, 95) if gender == "M" else random.randint(45, 78),
                bio=build_demo_bio(first, gender),
                is_face_verified=True,
                district=district,
                latitude=lat,
                longitude=lng,
            )
            if interests:
                profile.interests.set(random.sample(interests, min(4, len(interests))))
            if goals:
                profile.goals.set(random.sample(goals, min(2, len(goals))))

            sync_natural_profile_photo(user, gender, i if gender == "M" else i - 50)

            total_created += 1
            icon = "👨" if gender == "M" else "👩"
            self.stdout.write(f"  {icon} {first} {last} ({email}) yaratildi")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ {total_created} yangi foydalanuvchi yaratildi, {total_existing} mavjud profil yangilandi"
            )
        )

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
