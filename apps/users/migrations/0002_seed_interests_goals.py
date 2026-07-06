from django.db import migrations


INTERESTS = [
    ("Music", "Musiqa", "🎵"),
    ("Sport", "Sport", "⚽"),
    ("Travel", "Sayohat", "✈️"),
    ("Books", "Kitob", "📚"),
    ("Movies", "Kino", "🎬"),
    ("Food", "Ovqatlanish", "🍕"),
    ("Art", "Rasm chizish", "🎨"),
    ("Gaming", "Gaming", "🎮"),
    ("Animals", "Hayvonlar", "🐾"),
    ("Photography", "Fotografiya", "📷"),
    ("Dancing", "Raqs", "💃"),
    ("Nature", "Tabiat", "🌿"),
    ("Yoga", "Yoga", "🧘"),
    ("Technology", "Texnologiya", "💻"),
    ("Fashion", "Moda", "👗"),
]

GOALS = [
    ("Serious relationship", "Jiddiy munosabat", "💍"),
    ("Friendship", "Do'stlik", "🤝"),
    ("Chatting", "Suhbat va muloqot", "💬"),
    ("Casual fun", "Ko'ngilochar", "😊"),
    ("Marriage", "Nikoh", "💒"),
]


def seed(apps, schema_editor):
    Interest = apps.get_model('users', 'Interest')
    Goal = apps.get_model('users', 'Goal')

    if not Interest.objects.exists():
        Interest.objects.bulk_create([
            Interest(name=name, name_uz=name_uz, icon=icon)
            for name, name_uz, icon in INTERESTS
        ])

    if not Goal.objects.exists():
        Goal.objects.bulk_create([
            Goal(name=name, name_uz=name_uz, icon=icon)
            for name, name_uz, icon in GOALS
        ])


def unseed(apps, schema_editor):
    Interest = apps.get_model('users', 'Interest')
    Goal = apps.get_model('users', 'Goal')
    Interest.objects.filter(name__in=[n for n, _, _ in INTERESTS]).delete()
    Goal.objects.filter(name__in=[n for n, _, _ in GOALS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
