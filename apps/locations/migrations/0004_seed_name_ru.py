from django.db import migrations

# Viloyat: (name_uz, name_ru)
REGION_RU = {
    "Toshkent shahri":               "Ташкент (город)",
    "Toshkent viloyati":             "Ташкентская область",
    "Andijon viloyati":              "Андижанская область",
    "Farg'ona viloyati":             "Ферганская область",
    "Namangan viloyati":             "Наманганская область",
    "Samarqand viloyati":            "Самаркандская область",
    "Buxoro viloyati":               "Бухарская область",
    "Qashqadaryo viloyati":          "Кашкадарьинская область",
    "Surxondaryo viloyati":          "Сурхандарьинская область",
    "Jizzax viloyati":               "Джизакская область",
    "Sirdaryo viloyati":             "Сырдарьинская область",
    "Navoiy viloyati":               "Навоийская область",
    "Xorazm viloyati":               "Хорезмская область",
    "Qoraqalpog'iston Respublikasi": "Республика Каракалпакстан",
}

# Tuman: (name_uz, name_ru)
DISTRICT_RU = {
    # Toshkent shahri
    "Chilonzor":          "Чиланзар",
    "Yunusobod":          "Юнусабад",
    "Mirzo Ulug'bek":     "Мирзо-Улугбек",
    "Yakkasaroy":         "Яккасарай",
    "Shayxontohur":       "Шайхантахурский",
    # Toshkent viloyati
    "Bekobod":            "Бекабад",
    "Chirchiq":           "Чирчик",
    "Olmaliq":            "Алмалык",
    "Angren":             "Ангрен",
    "Yangiyo'l":          "Янгиюль",
    # Andijon
    "Andijon shahri":     "Андижан (город)",
    "Asaka":              "Асака",
    "Xo'jaobod":          "Хужаабад",
    "Marhamat":           "Мархамат",
    # Farg'ona
    "Farg'ona shahri":    "Фергана (город)",
    "Qo'qon":             "Коканд",
    "Marg'ilon":          "Маргилан",
    "Quvasoy":            "Кувасай",
    # Namangan
    "Namangan shahri":    "Наманган (город)",
    "Chust":              "Чуст",
    "Pop":                "Поп",
    "Kosonsoy":           "Касансай",
    # Samarqand
    "Samarqand shahri":   "Самарканд (город)",
    "Kattaqo'rg'on":      "Каттакурган",
    "Urgut":              "Ургут",
    "Bulung'ur":          "Булунгур",
    # Buxoro
    "Buxoro shahri":      "Бухара (город)",
    "Kogon":              "Каган",
    "G'ijduvon":          "Гиждуван",
    "Vobkent":            "Вабкент",
    # Qashqadaryo
    "Qarshi":             "Карши",
    "Shahrisabz":         "Шахрисабз",
    "Kitob":              "Китаб",
    "G'uzor":             "Гузар",
    # Surxondaryo
    "Termiz":             "Термез",
    "Denov":              "Денау",
    "Sherobod":           "Шерабад",
    "Boysun":             "Байсун",
    # Jizzax
    "Jizzax shahri":      "Джизак (город)",
    "Gagarin":            "Гагарин",
    "Do'stlik":           "Дустлик",
    "Zomin":              "Зомин",
    # Sirdaryo
    "Guliston":           "Гулистан",
    "Yangiyer":           "Янгиер",
    "Shirin":             "Ширин",
    "Sayxunobod":         "Сайхунабад",
    # Navoiy
    "Navoiy shahri":      "Навои (город)",
    "Zarafshon":          "Зарафшан",
    "Uchquduq":           "Учкудук",
    "Karmana":            "Кармана",
    # Xorazm
    "Urganch":            "Ургенч",
    "Xiva":               "Хива",
    "Shovot":             "Шават",
    "Bog'ot":             "Богот",
    # QQR
    "Nukus":              "Нукус",
    "Xo'jayli":           "Хужайли",
    "Beruniy":            "Беруний",
    "To'rtko'l":          "Турткуль",
}


def seed_ru(apps, schema_editor):
    Region = apps.get_model('locations', 'Region')
    District = apps.get_model('locations', 'District')
    Country = apps.get_model('locations', 'Country')

    Country.objects.filter(code='UZ').update(name_ru='Узбекистан')

    for name_uz, name_ru in REGION_RU.items():
        Region.objects.filter(name_uz=name_uz).update(name_ru=name_ru)

    for name_uz, name_ru in DISTRICT_RU.items():
        District.objects.filter(name_uz=name_uz).update(name_ru=name_ru)


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0003_add_name_ru'),
    ]

    operations = [
        migrations.RunPython(seed_ru, migrations.RunPython.noop),
    ]
