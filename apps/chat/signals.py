from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Message


@receiver(post_save, sender=Message)
def broadcast_new_message(sender, instance, created, **kwargs):
    """Yangi xabar QAYERDA yaratilishidan qat'i nazar — REST orqali
    (SendMessageView), WebSocket orqali (ChatConsumer) yoki Django admin
    panelidan (ChatRoomAdmin inline'dagi javob) — shu yerda BIR MARTA
    WebSocket guruhiga broadcast qilinadi. Shu tufayli admin xabarni
    panel orqali yozsa ham, foydalanuvchi chatda real vaqtda ko'radi."""
    if not created:
        return

    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(f'chat_{instance.room_id}', {
        'type':         'chat_message',
        'id':           instance.id,
        'sender_id':    instance.sender_id,
        'message_type': instance.message_type,
        'content':      instance.content,
        'reply_to_id':  instance.reply_to_id,
        'created_at':   instance.created_at.isoformat(),
    })
