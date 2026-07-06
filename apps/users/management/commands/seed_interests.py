from django.core.management.base import BaseCommand
from apps.users.models import Interest, Goal

INTERESTS = [
    ('Travel',     'Sayohat',     '✈️'),
    ('Music',      'Musiqa',      '🎵'),
    ('Sports',     'Sport',       '⚽'),
    ('Reading',    'Kitob',       '📚'),
    ('Cooking',    'Pazandachilik','🍳'),
    ('Photography','Fotografiya', '📸'),
    ('Movies',     'Kino',        '🎬'),
    ('Gaming',     'O\'yin',      '🎮'),
    ('Art',        'San\'at',     '🎨'),
    ('Fitness',    'Fitness',     '💪'),
]

GOALS = [
    ('Serious relationship', 'Jiddiy munosabat', '💍'),
    ('Friendship',           'Do\'stlik',        '🤝'),
    ('Dating',               'Suhbat',           '☕'),
    ('Marriage',             'Nikoh',            '💒'),
]


class Command(BaseCommand):
    help = 'Qiziqishlar va maqsadlarni yaratish'

    def handle(self, *args, **kwargs):
        for name, uz, icon in INTERESTS:
            Interest.objects.get_or_create(name=name, defaults={'name_uz': uz, 'icon': icon})
        for name, uz, icon in GOALS:
            Goal.objects.get_or_create(name=name, defaults={'name_uz': uz, 'icon': icon})
        self.stdout.write(self.style.SUCCESS('✅ Qiziqishlar va maqsadlar yaratildi.'))
