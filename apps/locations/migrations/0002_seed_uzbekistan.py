from django.db import migrations

# O'zbekiston: viloyatlar va ularning ba'zi tumanlari (qisqartirilgan ro'yxat)
REGIONS = {
    "Toshkent shahri": ["Chilonzor", "Yunusobod", "Mirzo Ulug'bek", "Yakkasaroy", "Shayxontohur"],
    "Toshkent viloyati": ["Bekobod", "Chirchiq", "Olmaliq", "Angren", "Yangiyo'l"],
    "Andijon viloyati": ["Andijon shahri", "Asaka", "Xo'jaobod", "Marhamat"],
    "Farg'ona viloyati": ["Farg'ona shahri", "Qo'qon", "Marg'ilon", "Quvasoy"],
    "Namangan viloyati": ["Namangan shahri", "Chust", "Pop", "Kosonsoy"],
    "Samarqand viloyati": ["Samarqand shahri", "Kattaqo'rg'on", "Urgut", "Bulung'ur"],
    "Buxoro viloyati": ["Buxoro shahri", "Kogon", "G'ijduvon", "Vobkent"],
    "Qashqadaryo viloyati": ["Qarshi", "Shahrisabz", "Kitob", "G'uzor"],
    "Surxondaryo viloyati": ["Termiz", "Denov", "Sherobod", "Boysun"],
    "Jizzax viloyati": ["Jizzax shahri", "Gagarin", "Do'stlik", "Zomin"],
    "Sirdaryo viloyati": ["Guliston", "Yangiyer", "Shirin", "Sayxunobod"],
    "Navoiy viloyati": ["Navoiy shahri", "Zarafshon", "Uchquduq", "Karmana"],
    "Xorazm viloyati": ["Urganch", "Xiva", "Shovot", "Bog'ot"],
    "Qoraqalpog'iston Respublikasi": ["Nukus", "Xo'jayli", "Beruniy", "To'rtko'l"],
}


def seed(apps, schema_editor):
    Country = apps.get_model('locations', 'Country')
    Region = apps.get_model('locations', 'Region')
    District = apps.get_model('locations', 'District')

    uz, _ = Country.objects.get_or_create(
        code='UZ', defaults={'name': 'Uzbekistan', 'name_uz': "O'zbekiston"}
    )
    if not uz.name_uz:
        uz.name_uz = "O'zbekiston"
        uz.save()

    if not Region.objects.filter(country=uz).exists():
        for region_name, districts in REGIONS.items():
            region = Region.objects.create(country=uz, name=region_name, name_uz=region_name)
            District.objects.bulk_create([
                District(region=region, name=d, name_uz=d) for d in districts
            ])


def unseed(apps, schema_editor):
    Country = apps.get_model('locations', 'Country')
    Country.objects.filter(code='UZ').delete()  # cascades to regions/districts


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
