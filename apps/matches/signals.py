from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Match


@receiver(post_save, sender=Match)
def create_chat_room_for_match(sender, instance, created, **kwargs):
    """Yangi Match yaratilganda (qoidan API orqali bo'lsin, Django admin
    paneli orqali qo'lda yaratilgan bo'lsin) avtomatik ChatRoom ochadi va
    ikki tomonni participant qilib qo'shadi. Shu tufayli admin panelidan
    "Matches -> Add match" orqali ikki foydalanuvchini tanlab saqlash
    kifoya — chat o'zi paydo bo'ladi."""
    if not created:
        return
    from apps.chat.models import ChatRoom

    room, _ = ChatRoom.objects.get_or_create(
        match=instance, defaults={'room_type': 'match'}
    )
    room.participants.set([instance.user1, instance.user2])
