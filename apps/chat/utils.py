"""Chat uchun yordamchi funksiyalar: obuna darajasiga qarab chat muddati
("3 kun / 1 hafta / 1 oy") va har bir foydalanuvchi uchun doimiy ochiq
turadigan "Admin" (yordam) xonasi.

Muddat qiymatlari endi kodda qattiq yozilmagan — admin panelda
Subscriptions > Plans bo'limidan har bir tarif (Free/Premium/VIP) uchun
alohida `chat_duration_days` sifatida ko'rish/o'zgartirish mumkin.
"""
from datetime import timedelta

from django.utils import timezone

# Agar "free" Plan qatori DBda topilmasa (masalan seed_plans hali
# ishlamagan bo'lsa) ishlatiladigan xavfsiz standart qiymat.
_FALLBACK_CHAT_DAYS = 3


def user_plan_type(user):
    """Foydalanuvchining joriy faol tarif turi ('free' / 'premium' / 'vip')."""
    sub = getattr(user, 'subscription', None)
    if sub and sub.is_active:
        return sub.plan.plan_type
    return 'free'


def user_chat_duration_days(user):
    """Foydalanuvchining joriy faol tarifiga ko'ra chat necha kun ochiq
    turishi. Qiymat admin paneldagi `Plan.chat_duration_days` dan olinadi —
    Free/Premium/VIP uchun alohida sozlanadi (kodda qattiq emas)."""
    sub = getattr(user, 'subscription', None)
    if sub and sub.is_active:
        return sub.plan.chat_duration_days

    from apps.subscriptions.models import Plan

    free_plan = Plan.objects.filter(plan_type='free').only('chat_duration_days').first()
    return free_plan.chat_duration_days if free_plan else _FALLBACK_CHAT_DAYS


def room_lock_state(room, user):
    """
    `user` nuqtai nazaridan `room` qulflanganmi (muddati tugaganmi) va
    qachon tugashini qaytaradi: (is_locked: bool, expires_at: datetime|None).

    Admin (yordam) xonasi hech qachon qulflanmaydi — har doim ochiq.
    """
    if room.room_type == 'admin':
        return False, None
    days = user_chat_duration_days(user)
    expires_at = room.created_at + timedelta(days=days)
    return timezone.now() > expires_at, expires_at


def room_blocked_other(room, user):
    """`room` ichidagi ikkinchi ishtirokchi bilan `user` orasida (ikki
    tomonlama) faol bloklash bor-yo'qligini tekshiradi. Admin xonasida hech
    qachon bloklanmaydi (ikkinchi haqiqiy ishtirokchi yo'q)."""
    if room.room_type == 'admin':
        return False
    from apps.users.models import Block

    other = room.participants.exclude(pk=user.pk).first()
    if not other:
        return False
    return Block.is_blocked_between(user, other)


def room_muted_by(room, user):
    """`user` shu `room` uchun bildirishnomalarni o'chirib qo'yganmi —
    `SendMessageView`/`ScreenshotAlertView`/`ReplyToStoryView` shu yerga
    qarab push/in-app bildirishnoma yuborish-yubormaslikni hal qiladi.
    MUHIM: bu FAQAT bildirishnomaga ta'sir qiladi — xabarning o'zi (WS/chat
    ichida) har doim oddiy tarzda yetib boradi."""
    return room.muted_by.filter(pk=user.pk).exists()


def get_clear_timestamp(room, user):
    """`user` `room`ni qachon "tozalagani" (`ChatClear.cleared_at`) — shu
    vaqtdan OLDINGI xabarlar unga ko'rsatilmaydi (MessageListView/qidiruv/
    ChatRoomSerializer shu yerga qarab filtrlaydi). Tozalanmagan bo'lsa
    `None` qaytadi. MUHIM: bu hech qachon `Message` qatorlarini o'chirmaydi —
    faqat shu foydalanuvchiga ko'rsatishni filtrlash uchun ishlatiladi."""
    from .models import ChatClear

    clear = ChatClear.objects.filter(room=room, user=user).only('cleared_at').first()
    return clear.cleared_at if clear else None


def get_or_create_match_room(user_a, user_b):
    """`user_a` va `user_b` orasidagi 'match' turidagi ChatRoom'ni topadi.
    Odatda bu allaqachon mavjud bo'ladi — Match yaratilganda post_save signal
    orqali avtomatik tug'iladi (masalan story-javob yuborilishidan oldin
    story-feed ko'rinishi uchun ikki tomon matched bo'lishi shart). Lekin har
    ehtimolga qarshi (eski ma'lumotlar yoki signal ishlamagan holat) topilmasa,
    shu ikkisi ishtirokchi bo'lgan yangi xona yaratib beradi — `ensure_admin_room`
    bilan bir xil "topish yoki yaratish" uslubida."""
    from .models import ChatRoom

    room = ChatRoom.objects.filter(
        room_type='match', participants=user_a
    ).filter(participants=user_b).first()
    if room:
        return room
    room = ChatRoom.objects.create(room_type='match')
    room.participants.add(user_a, user_b)
    return room


def ensure_admin_room(user):
    """Foydalanuvchi uchun "Yordam" (admin) xonasini topadi yoki yaratadi.
    Ikkinchi ishtirokchi shart emas — UI buni maxsus "Admin/Yordam" yorlig'i
    bilan ko'rsatadi (ChatRoomSerializer.get_other_user 'admin' turini
    alohida holat sifatida ko'rib chiqadi va doim None qaytaradi)."""
    from .models import ChatRoom

    room = ChatRoom.objects.filter(room_type='admin', participants=user).first()
    if room:
        return room
    room = ChatRoom.objects.create(room_type='admin')
    room.participants.add(user)
    return room
