from datetime import timedelta

from django.db import models
from django.conf import settings
from django.utils import timezone


class ChatRoom(models.Model):
    ROOM_TYPES = [('match', 'Match'), ('admin', 'Admin')]

    room_type    = models.CharField(max_length=10, choices=ROOM_TYPES, default='match')
    match        = models.OneToOneField(
        'matches.Match', on_delete=models.CASCADE,
        null=True, blank=True, related_name='chat_room'
    )
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_rooms')
    # Bildirishnomalarni shu xona uchun o'chirib qo'ygan foydalanuvchilar.
    # MUHIM: bu FAQAT push/in-app bildirishnoma yuborilishini boshqaradi —
    # xabarlarning o'zi (WebSocket/chat ichida) har doim oddiy tarzda
    # davom etadi, hech narsa o'chirilmaydi yoki bloklanmaydi.
    muted_by     = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='muted_chat_rooms', blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatRoom #{self.pk} [{self.room_type}]"

    def last_message(self):
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    MSG_TEXT     = 'text'
    MSG_IMAGE    = 'image'
    MSG_VIDEO    = 'video'
    MSG_VOICE    = 'voice'
    MSG_LOCATION = 'location'
    MSG_DISAPPEARING_PHOTO = 'disappearing_photo'
    MSG_SYSTEM   = 'system'
    MSG_STORY_REPLY = 'story_reply'
    MSG_VIDEO_NOTE = 'video_note'
    MSG_TYPES = [
        (MSG_TEXT,     'Matn'),
        (MSG_IMAGE,    'Rasm'),
        (MSG_VIDEO,    'Video'),
        (MSG_VOICE,    'Ovozli'),
        (MSG_LOCATION, 'Joylashuv'),
        (MSG_DISAPPEARING_PHOTO, "O'chib ketadigan rasm"),
        (MSG_SYSTEM,   'Tizim xabari'),
        (MSG_STORY_REPLY, 'Storyga javob'),
        (MSG_VIDEO_NOTE, 'Video xabar (doira)'),
    ]

    room         = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=20, choices=MSG_TYPES, default=MSG_TEXT)
    content      = models.TextField(blank=True)
    media        = models.FileField(upload_to='chat_media/%Y/%m/', null=True, blank=True)
    # Faqat voice/video uchun — qurilmada YOZILGAN haqiqiy davomiylik (soniya).
    # Buni saqlab qo'yish MUHIM: agar mijoz davomiylikni faylning o'zidan
    # (remote URL orqali AVURLAsset.load(.duration) bilan) qayta hisoblashga
    # urinsa, ba'zi serverlar/fayl formatlarida bu ishonchsiz (range so'rovlar
    # qo'llab-quvvatlanmasa yoki moov atom oxirida bo'lsa, 0 qaytaradi) — shu
    # sababli yozish vaqtida bilingan qiymatni to'g'ridan-to'g'ri saqlaymiz.
    duration     = models.FloatField(null=True, blank=True)
    # Faqat message_type='location' uchun to'ldiriladi (boshqa turlarda bo'sh qoladi).
    latitude     = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude    = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # Faqat message_type='disappearing_photo' uchun: ko'rish uchun tanlangan
    # davomiylik (3/5/10 soniya) va birinchi marta ochilgan vaqt. MUHIM: rasm
    # (fayl) va shu Message qatori bazadan HECH QACHON o'chirilmaydi — faqat
    # `disappear_expired` xossasi orqali (vaqt hisoblab) ko'rsatishga ruxsat
    # berilmaydi, klient holatiga (masalan ilova yopilib qolishiga) bog'liq
    # bo'lmagan ishonchli usul.
    disappear_seconds = models.PositiveSmallIntegerField(null=True, blank=True)
    viewed_at    = models.DateTimeField(null=True, blank=True)
    # Qulflanib qolgan keshlovchi belgi — `disappear_expired` bilan birga
    # ishlatiladi, lekin yagona manba sifatida emas (har doim vaqt asosida
    # qayta hisoblanadi).
    is_expired   = models.BooleanField(default=False)
    reply_to     = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    # Faqat message_type='story_reply' uchun: javob yozilgan story. `SET_NULL`
    # — soft-delete qoidasiga ko'ra, story (yoki uning o'zi) keyinchalik
    # o'chirilsa ham (faqat is_deleted orqali), bu Message qatori HECH QACHON
    # bazadan o'chirilmaydi; story FK shunchaki bo'shab qoladi.
    story        = models.ForeignKey(
        'stories.Story', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='chat_replies',
    )
    is_deleted   = models.BooleanField(default=False)
    # Matn tahrirlangan bo'lsa belgilanadi (EditMessageView) — faqat suhbatda
    # "tahrirlangan" yorlig'ini ko'rsatish uchun. MUHIM: tahrirlash ham
    # qattiq qoidaga bo'ysunadi — Message qatorining o'zi HECH QACHON
    # o'chirilmaydi yoki yangi qator bilan almashtirilmaydi, faqat shu
    # qatordagi `content`ning o'zi yangilanadi.
    is_edited    = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.message_type}] {self.sender} → Room#{self.room_id}"

    @property
    def disappear_expired(self):
        """O'chib ketadigan rasm ko'rsatishga yaroqsiz bo'lib qolganmi —
        ko'rilmagan bo'lsa hali yaroqli (False); birinchi ko'rilgandan keyin
        `disappear_seconds` o'tgan bo'lsa, doimiy ravishda yaroqsiz."""
        if self.message_type != self.MSG_DISAPPEARING_PHOTO:
            return False
        if self.is_expired:
            return True
        if not self.viewed_at or not self.disappear_seconds:
            return False
        return timezone.now() > self.viewed_at + timedelta(seconds=self.disappear_seconds)


class MessageRead(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reads')
    user    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']


class ChatClear(models.Model):
    """Foydalanuvchi "Chatni tozalash"ni bosgan lahzasi — FAQAT shu
    foydalanuvchi uchun, shu vaqtdan OLDINGI xabarlarni ko'rsatishni
    to'xtatadi (MessageListView/ChatRoomSerializer shu yerga qarab filtrlaydi).
    MUHIM: bu hech qachon `Message` qatorlarini bazadan o'chirmaydi yoki
    o'zgartirmaydi — suhbatdosh tomonida hech narsa o'zgarmaydi, xabarlar
    butunlay saqlanib qoladi. Foydalanuvchi qayta "tozalasa", shu yerdagi
    `cleared_at` shunchaki yangi (kechroq) vaqtga yangilanadi."""
    room       = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='clears')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_clears')
    cleared_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['room', 'user']]
