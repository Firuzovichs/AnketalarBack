from django.db import migrations

# (name_uz, name_ru)
INTEREST_RU = {
    "Musiqa":        "Музыка",
    "Sport":         "Спорт",
    "Sayohat":       "Путешествия",
    "Kitob":         "Книги",
    "Kino":          "Кино",
    "Ovqatlanish":   "Еда",
    "Rasm chizish":  "Рисование",
    "Gaming":        "Игры",
    "Hayvonlar":     "Животные",
    "Fotografiya":   "Фотография",
    "Raqs":          "Танцы",
    "Tabiat":        "Природа",
    "Yoga":          "Йога",
    "Texnologiya":   "Технологии",
    "Moda":          "Мода",
}

GOAL_RU = {
    "Jiddiy munosabat":   "Серьёзные отношения",
    "Do'stlik":           "Дружба",
    "Suhbat va muloqot":  "Общение",
    "Ko'ngilochar":       "Развлечения",
    "Nikoh":              "Брак",
}


def seed_ru(apps, schema_editor):
    Interest = apps.get_model('users', 'Interest')
    Goal = apps.get_model('users', 'Goal')

    for name_uz, name_ru in INTEREST_RU.items():
        Interest.objects.filter(name_uz=name_uz).update(name_ru=name_ru)

    for name_uz, name_ru in GOAL_RU.items():
        Goal.objects.filter(name_uz=name_uz).update(name_ru=name_ru)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_add_name_ru'),
    ]

    operations = [
        migrations.RunPython(seed_ru, migrations.RunPython.noop),
    ]
