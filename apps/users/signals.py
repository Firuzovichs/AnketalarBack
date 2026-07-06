from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import User


@receiver(post_save, sender=User)
def create_admin_chat(sender, instance, created, **kwargs):
    """Yangi user yaratilganda admin bilan chat ochish."""
    if created:
        from apps.chat.models import ChatRoom
        try:
            admin = User.objects.filter(is_staff=True).first()
            if admin:
                room = ChatRoom.objects.create(room_type='admin')
                room.participants.set([instance, admin])
        except Exception:
            pass
