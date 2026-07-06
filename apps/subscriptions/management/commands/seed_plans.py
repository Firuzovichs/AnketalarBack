from django.core.management.base import BaseCommand
from apps.subscriptions.models import Plan


class Command(BaseCommand):
    help = 'Boshlang\'ich tarif rejalarini yaratish'

    def handle(self, *args, **kwargs):
        Plan.get_defaults()
        self.stdout.write(self.style.SUCCESS('✅ Tarif rejalari yaratildi.'))
