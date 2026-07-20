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
    panel orqali yozsa ham, foydalanuvchi chatda real vaqtda ko'radi.

    MUHIM: to'liq MessageSerializer orqali serialize qilinadi — shunda
    `reply_to` (nested), `sender` (nested), `media` va boshqa barcha
    maydonlar mijozga (iOS/Android) to'g'ri yetib boradi. Avvalgi
    minimal payload (faqat `id`, `sender_id`, `reply_to_id`) ishlatilmaydi
    — chunki u nested ob'ektlarsiz kelardi va reply ko'rinmasdi."""
    if not created:
        return

    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    # N+1 muammosidan qochish uchun zarur related fieldlarni oldindan yuklaymiz
    from .models import Message as Msg
    from .serializers import MessageSerializer
    try:
        msg_obj = Msg.objects.select_related(
            'sender',
            'sender__profile',
            'reply_to',
            'reply_to__sender',
            'reply_to__sender__profile',
            'story',
        ).get(pk=instance.pk)
        msg_data = MessageSerializer(msg_obj).data
    except Exception:
        # Serialize xato bo'lsa — minimal fallback (reply ko'rinmasa ham xabar boradi)
        msg_data = {
            'id':           instance.id,
            'room':         instance.room_id,
            'message_type': instance.message_type,
            'content':      instance.content,
            'created_at':   instance.created_at.isoformat() if instance.created_at else None,
        }

    async_to_sync(channel_layer.group_send)(f'chat_{instance.room_id}', {
        'type':    'chat_message',
        'message': msg_data,
    })
