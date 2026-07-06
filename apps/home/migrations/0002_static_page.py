from django.db import migrations, models


ABOUT_CONTENT = (
    "Anketalar — odamlarni bir-biriga yaqinlashtirish uchun yaratilgan tanishuv ilovasi.\n\n"
    "Maqsadimiz — xavfsiz, qulay va samimiy muhitda yangi tanishlar orttirish imkonini berish. "
    "Ilova orqali siz qiziqishlaringizga mos insonlarni topishingiz, suhbatlashishingiz va "
    "yangi munosabatlar boshlashingiz mumkin.\n\n"
    "Savol va takliflar bo'yicha biz bilan bog'lanishingiz mumkin."
)

TERMS_CONTENT = (
    "Diqqat: bu matn vaqtinchalik namuna sifatida joylangan va yuridik jihatdan tasdiqlanmagan. "
    "Ilovadan foydalanishdan oldin ushbu bo'lim mas'ul yurist tomonidan ko'rib chiqilishi va "
    "to'liq matn bilan almashtirilishi tavsiya etiladi.\n\n"
    "1. Ilovadan foydalanish orqali siz quyidagi shartlarga rozilik bildirasiz.\n"
    "2. Foydalanuvchi ilovada haqiqiy va to'g'ri ma'lumot kiritishi shart.\n"
    "3. Boshqa foydalanuvchilarga nisbatan hurmatsizlik, tahdid yoki firibgarlik taqiqlanadi.\n"
    "4. Qoidabuzarlik aniqlangan taqdirda hisob bloklanishi mumkin."
)

PRIVACY_CONTENT = (
    "Diqqat: bu matn vaqtinchalik namuna sifatida joylangan va yuridik jihatdan tasdiqlanmagan. "
    "Ilovadan foydalanishdan oldin ushbu bo'lim mas'ul yurist tomonidan ko'rib chiqilishi va "
    "to'liq matn bilan almashtirilishi tavsiya etiladi.\n\n"
    "1. Sizning shaxsiy ma'lumotlaringiz faqat ilova ichidagi xizmatlarni taqdim etish uchun ishlatiladi.\n"
    "2. Ma'lumotlaringiz uchinchi shaxslarga sotilmaydi.\n"
    "3. Joylashuv va profil ma'lumotlari faqat siz ruxsat bergan doirada boshqa foydalanuvchilarga ko'rsatiladi.\n"
    "4. Hisobni o'chirishni so'ragan foydalanuvchining ma'lumotlari tasdiqlangandan so'ng faolsizlantiriladi."
)


def seed(apps, schema_editor):
    StaticPage = apps.get_model('home', 'StaticPage')
    StaticPage.objects.bulk_create([
        StaticPage(slug='about', title="Biz haqimizda", content=ABOUT_CONTENT),
        StaticPage(slug='terms', title="Foydalanish shartlari", content=TERMS_CONTENT),
        StaticPage(slug='privacy', title="Maxfiylik siyosati", content=PRIVACY_CONTENT),
    ])


def unseed(apps, schema_editor):
    StaticPage = apps.get_model('home', 'StaticPage')
    StaticPage.objects.filter(slug__in=['about', 'terms', 'privacy']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StaticPage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(choices=[('about', 'Biz haqimizda'), ('terms', 'Foydalanish shartlari'), ('privacy', 'Maxfiylik siyosati')], max_length=30, unique=True, verbose_name='Slug')),
                ('title', models.CharField(max_length=200, verbose_name='Sarlavha')),
                ('content', models.TextField(verbose_name='Kontent')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqti')),
            ],
            options={
                'verbose_name': 'Statik sahifa',
                'verbose_name_plural': 'Statik sahifalar',
                'ordering': ['slug'],
            },
        ),
        migrations.RunPython(seed, unseed),
    ]
