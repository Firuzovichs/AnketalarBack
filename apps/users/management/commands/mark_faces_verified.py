from django.core.management.base import BaseCommand
from apps.users.models import UserProfile


class Command(BaseCommand):
    help = (
        "Test/seed foydalanuvchilarning is_face_verified holatini True qilib belgilaydi "
        "(face-scan flow'dan o'tmagan profillar qidiruv/xarita natijalarida ko'rinishi uchun)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--only-with-coords',
            action='store_true',
            help="Faqat joylashuvi (latitude/longitude) saqlangan profillarni belgilaydi.",
        )
        parser.add_argument(
            '--emails',
            nargs='+',
            help="Faqat shu email manzillariga tegishli foydalanuvchilarni belgilaydi.",
        )

    def handle(self, *args, **options):
        qs = UserProfile.objects.filter(is_face_verified=False)

        if options.get('emails'):
            qs = qs.filter(user__email__in=options['emails'])
        elif options.get('only_with_coords'):
            qs = qs.filter(latitude__isnull=False, longitude__isnull=False)

        count = qs.update(is_face_verified=True)
        self.stdout.write(self.style.SUCCESS(
            f"✅ {count} ta profil yuz tasdiqlangan (is_face_verified=True) deb belgilandi."
        ))
